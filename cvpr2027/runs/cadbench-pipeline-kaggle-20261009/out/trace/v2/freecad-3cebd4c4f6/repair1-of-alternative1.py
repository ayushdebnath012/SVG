"""
answer.py
FreeCAD 1.1 Script to generate a Round Key part.
The script builds a parametric PartDesign feature tree inside a single Body.
"""

from pathlib import Path
import FreeCAD as App
import Part
import Sketcher

def main():
    # Create a new document
    doc = App.newDocument("RoundKey")

    # 1. Create Parameters
    params = doc.addObject("App::VarSet", "Parameters")
    params.addProperty("App::PropertyLength", "diameter", "Dimensions", "Key outer diameter")
    params.addProperty("App::PropertyLength", "height", "Dimensions", "Key height (axial length)")
    params.addProperty("App::PropertyLength", "length", "Dimensions", "Key depth (radial length)")
    params.addProperty("App::PropertyLength", "radius", "Dimensions", "Calculated radius for sketch")
    
    params.diameter = 5.0
    params.height = 3.0
    params.length = 10.0
    params.radius = params.diameter / 2.0

    # Set expressions to keep radius in sync with diameter
    params.setExpression("radius", "Parameters.diameter / 2")

    # 2. Create Body
    body = doc.addObject("PartDesign::Body", "Body")

    # 3. Create Base Sketch on XY Plane
    # In FreeCAD 1.1, the standard planes (XY_Plane, etc.) are available in the document.
    xy_plane = doc.getObject("XY_Plane")
    if not xy_plane:
        raise RuntimeError("XY_Plane not found in document. Standard planes might be missing.")

    sketch = body.newObject("Sketcher::SketchObject", "BaseSketch")
    # AttachmentSupport must be a tuple of (Object, [FaceIndex])
    sketch.AttachmentSupport = (xy_plane, [""])
    # Placement for the sketch object itself (offset from the plane)
    sketch.Placement = App.Placement(App.Vector(0, 0, 0))
    sketch.MapMode = "FlatFace"
    
    # Add Geometry: Circle
    sketch.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.radius), False)
    
    # Add Constraints: Center the circle at the origin
    # Constraint ID 0 refers to the first point of the first geometry (the circle center)
    sketch.addConstraint(Sketcher.Constraint("Point", 0, "XY_Plane.Origin"))
    
    # Force update of sketch geometry
    sketch.updateGeometry()

    # 4. Create Pad Feature
    # This creates the main cylindrical body.
    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile = sketch
    # Use the 'height' parameter for the length of the pad
    pad.setExpression("Length", "Parameters.height")
    
    # 5. Create Hole Feature (for the shaft fit)
    # We create a sketch on the top face of the Pad.
    # To do this robustly in headless mode, we attach the sketch to the XY plane 
    # but offset the placement by the height of the key.
    
    hole_sketch = body.newObject("Sketcher::SketchObject", "HoleSketch")
    hole_sketch.AttachmentSupport = (xy_plane, [""])
    # Offset the sketch to the top of the pad
    hole_sketch.Placement = App.Placement(App.Vector(0, 0, params.height))
    hole_sketch.MapMode = "FlatFace"
    
    # Add Geometry: Smaller circle for the hole
    # 0.5mm clearance
    hole_radius = params.diameter / 2.0 - 0.5 
    hole_sketch.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), hole_radius), False)
    
    # Constraint: Center the hole
    hole_sketch.addConstraint(Sketcher.Constraint("Point", 0, "XY_Plane.Origin"))
    hole_sketch.updateGeometry()
    
    # Create the Pocket
    pocket = body.newObject("PartDesign::Pocket", "Hole")
    pocket.Profile = hole_sketch
    pocket.Type = "ThroughAll" # Drill completely through

    # 6. Finalize
    doc.recompute()
    
    # Determine output path
    # The requirement is to save next to the script.
    script_path = Path(__file__).resolve()
    output_path = script_path.parent / f"{script_path.stem}.FCStd"
    
    # Ensure the file is saved to the correct location
    doc.saveAs(str(output_path))
    
    # Clean up
    App.closeDocument(doc.Name)
    App.quit()

if __name__ == "__main__":
    main()
