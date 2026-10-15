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
    
    # --- 5. Pad Feature (Flange Body) ---
    pad = body.newObject("PartDesign::Pad", "FlangePad")
    pad.Profile = base_sketch
    pad.Length = params.flange_thickness
    pad.Type = "Solid"
    
    # --- 6. Bolt Hole Sketch ---
    # We need to attach this sketch to the Top Face of the Pad to ensure the pocket 
    # starts from the top surface.
    # In FreeCAD 1.1 headless, we can access the face by index. 
    # For a simple Pad, the top face is typically index 1 (0 is bottom, 1 is top).
    # We will try to get the face object.
    
    # Get the top face of the Pad. 
    # The Pad object has a 'Faces' property or we can iterate? 
    # In FreeCAD 1.1, we can use the 'Face' property of the Body if available, 
    # but usually we access faces via the feature's 'Faces' list if exposed, or by index.
    # Let's try to get the face by index from the Pad's geometry.
    # A reliable way in headless is to use the 'Face' property of the Body if available, 
    # but usually we access faces via the feature's 'Faces' list if exposed, or by index.
    # Let's try to get the face object directly.
    
    # Workaround: Create the sketch on the XY plane.
    # Create the Pocket.
    # Set Type = "Through All".
    # Set Reference to the BoltSketch.
    # To ensure it cuts from the top, we can set the sketch plane to the Top Face directly.
    
    # Let's try to grab the face index. Usually, for a simple Pad, the top face is the last created or index 1.
    # But to be safe, let's create the sketch on the XY plane and use "Through All" without specific face attachment.
    # This works geometrically but the tree might show XY_Plane as support.
    # To be precise, let's try to attach to the Top Face.
    
    # Workaround for Headless Face Attachment:
    # Create the sketch on the XY plane.
    # Create the Pocket.
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
    
    bolt_sketch = body.newObject("Sketcher::SketchObject", "BoltSketch")
    bolt_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
    
    bolt_hole = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.bolt_hole_diameter / 2.0)
    bolt_sketch.addGeometry(bolt_hole, True)

    # --- 7. Bolt Hole Pattern ---
    # We need to pattern the hole.
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

    # --- 8. Compute and Save ---
    doc.recompute()
    
    # Save to the exact path derived from __file__
    # The prompt asks to save as answer.FCStd next to the script.
    output_path = os.path.splitext(__file__)[0] + ".FCStd"
    doc.saveAs(output_path)
    
    print(f"Model saved to {output_path}")

if __name__ == "__main__":
    main()
