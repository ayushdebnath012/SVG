import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

def create_large_washer():
    # Create a new document
    doc = App.newDocument("Washer")

    # Define parameters using App::VarSet which is the correct type for named parameters in PartDesign
    params = doc.addObject("App::VarSet", "Parameters")
    params.addProperty("App::PropertyLength", "outer_diameter", "Dimensions", "Outer diameter of the washer")
    params.addProperty("App::PropertyLength", "inner_diameter", "Dimensions", "Inner diameter of the washer (hole)")
    params.addProperty("App::PropertyLength", "thickness", "Dimensions", "Thickness of the washer")
    params.outer_diameter = 9.0
    params.inner_diameter = 3.2
    params.thickness = 0.8

    # Create a PartDesign Body
    body = doc.addObject("PartDesign::Body", "Body")

    # Create the base sketch on the XY plane
    sketch = body.newObject("Sketcher::SketchObject", "BaseSketch")
    # In FreeCAD 1.1, AttachmentSupport is a tuple of (SupportObject, [FaceIndex])
    # We use the XY_Plane which should exist in the document or be created implicitly if not found, 
    # but standard practice is to reference existing planes. If not present, we might need to create them or use a different method.
    # However, PartDesign::Body usually creates the standard planes. Let's try referencing XY_Plane.
    # If XY_Plane doesn't exist, we can create it via PartDesign::Plane, but the prompt implies standard usage.
    # Let's assume standard planes exist or create them if necessary. 
    # To be safe and robust in headless mode without GUI workbenches, we often create the plane explicitly or rely on the Body's default.
    # The most robust way in headless PartDesign is often to attach to a Plane object.
    
    # Let's create the XY_Plane explicitly to ensure it exists.
    xy_plane = doc.addObject("PartDesign::Plane", "XY_Plane")
    xy_plane.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
    doc.recompute()

    sketch.Plane = "XY_Plane"
    sketch.MapMode = "FlatFace"
    
    # Add outer circle geometry
    outer_radius = params.outer_diameter / 2.0
    inner_radius = params.inner_diameter / 2.0
    
    outer_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), outer_radius)
    sketch.addGeometry(outer_circle, False)
    
    inner_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), inner_radius)
    sketch.addGeometry(inner_circle, False)
    
    # Add constraints
    # Coincident centers
    sketch.addConstraint(Sketcher.Constraint("Coincident", 0, "Center", 1, "Center"))
    # Concentric
    sketch.addConstraint(Sketcher.Constraint("Concentric", 0, 1))
    
    # Fix sizes to parameters
    sketch.addConstraint(Sketcher.Constraint("Size", 0, "OuterRadius", "Parameters.outer_diameter/2"))
    sketch.addConstraint(Sketcher.Constraint("Size", 1, "OuterRadius", "Parameters.inner_diameter/2"))

    # Pad the sketch to create the washer thickness
    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile = sketch
    pad.Length = params.thickness
    # Drive length from parameter
    pad.setExpression("Length", "Parameters.thickness")

    # Recalculate to ensure the body is created correctly
    doc.recompute()
    
    # Save the document
    script_path = Path(__file__).resolve()
    output_path = script_path.parent / f"{script_path.stem}.FCStd"
    
    doc.saveAs(str(output_path))

if __name__ == "__main__":
    create_large_washer()
