"""
FreeCAD 1.1 Script: Parametric Headless Pin
Generates an editable PartDesign::Body with sketches and features.
"""

import os
from pathlib import Path
import FreeCAD as App
import Part
import Sketcher

def create_pin():
    # Initialize Document
    doc = App.newDocument("Pin")
    App.setActiveDocument(doc)

    # 1. Define Parameters (App::VarSet)
    params = doc.addObject("App::VarSet", "Parameters")
    params.addProperty("App::PropertyLength", "pin_diameter", "Dimensions", "Pin diameter")
    params.pin_diameter = 3.0
    
    params.addProperty("App::PropertyLength", "pin_length", "Dimensions", "Pin total length")
    params.pin_length = 6.0
    
    params.addProperty("App::PropertyLength", "chamfer_length", "Dimensions", "Chamfer length along axis")
    params.chamfer_length = 1.0
    
    params.addProperty("App::PropertyAngle", "chamfer_angle", "Dimensions", "Chamfer angle from horizontal")
    params.chamfer_angle = 30.0

    # 2. Create PartDesign Body
    body = doc.addObject("PartDesign::Body", "Body")
    # Correct Placement initialization for FreeCAD 1.1
    body.Placement = App.Placement(App.Vector(0, 0, 0))

    # 3. Create Base Sketch (Cylindrical Profile)
    sketch_base = body.newObject("Sketcher::SketchObject", "Sketch_Base")
    sketch_base.Placement = App.Placement(App.Vector(0, 0, 0))
    sketch_base.Support = (doc.getObject("XY_Plane"), [""]) 
    sketch_base.MapMode = "FlatFace"
    
    # Add Geometry: Circle
    # Radius is half of diameter
    radius = params.pin_diameter / 2.0
    circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), radius)
    sketch_base.addGeometry(circle, False)
    
    # Add Constraints to center the circle
    # Constraint: Point on Circle Center (0, 1) coincident with Origin (1, 1)
    c1 = Sketcher.Constraint("Point", 0, 1, 1, 1)
    # Constraint: Point on Circle Center (0, 1) coincident with Origin (1, 2)
    c2 = Sketcher.Constraint("Point", 0, 1, 1, 2)
    sketch_base.addConstraint(c1)
    sketch_base.addConstraint(c2)

    # 4. Create PartDesign Pad
    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile = sketch_base
    pad.Length = params.pin_length
    # Ensure Length is driven by parameter
    pad.setExpression("Length", "Parameters.pin_length")

    # 5. Create Chamfer Feature
    # We will use the Chamfer feature directly on the top edge of the pad.
    # Type "Angle" requires Size (distance along the edge) and Angle.
    chamfer = body.newObject("PartDesign::Chamfer", "Chamfer")
    chamfer.Type = "Angle"
    chamfer.setExpression("Size", "Parameters.chamfer_length")
    chamfer.setExpression("Angle", "Parameters.chamfer_angle")
    
    # Select the top edge of the pad. 
    # In a fresh tree, the top edge of the pad is typically the first edge of the pad object.
    # We reference the Pad object and the first edge.
    chamfer.Base = [pad, ["Edge1"]]

    # 6. Recompute to generate geometry
    doc.recompute()

    # 7. Save
    script_path = Path(__file__).resolve()
    output_path = script_path.parent / f"{script_path.stem}.FCStd"
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    doc.saveAs(str(output_path))
    print(f"Model saved to: {output_path}")

if __name__ == "__main__":
    create_pin()
