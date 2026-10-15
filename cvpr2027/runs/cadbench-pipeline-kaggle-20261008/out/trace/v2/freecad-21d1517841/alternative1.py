import os
import sys
import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Ensure we are in the correct environment for FreeCAD 1.1
# This script is designed to be run headlessly or via FreeCAD's macro system.

def create_large_washer():
    # Create a new document
    doc = App.newDocument("Washer")
    
    # Define parameters object for easy editing
    params = doc.addObject("App::Parameter", "Parameters")
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
    sketch.Plane = "XY_Plane"
    sketch.MapMode = "FlatFace"
    
    # Add outer circle geometry
    outer_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.outer_diameter / 2.0)
    sketch.addGeometry(outer_circle, False)
    
    # Add inner circle geometry
    inner_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.inner_diameter / 2.0)
    sketch.addGeometry(inner_circle, False)
    
    # Add constraints to define the relationship between circles
    # Coincident centers
    sketch.addConstraint(Sketcher.Constraint("Coincident", 0, "Center", 1, "Center"))
    
    # Concentric circles
    sketch.addConstraint(Sketcher.Constraint("Concentric", 0, 1))
    
    # Fix outer circle size to parameter
    sketch.addConstraint(Sketcher.Constraint("Size", 0, "OuterRadius", "Dimensions.outer_diameter/2"))
    sketch.addConstraint(Sketcher.Constraint("Size", 1, "OuterRadius", "Dimensions.inner_diameter/2"))

    # Pad the sketch to create the washer thickness
    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile = sketch
    pad.Length = params.thickness
    # Expressions can be used to drive the length from parameters
    pad.setExpression("Length", "Parameters.thickness")

    # Recalculate to ensure the body is created correctly
    doc.recompute()
    
    # Save the document
    script_path = Path(__file__).resolve()
    output_path = script_path.parent / f"{script_path.stem}.FCStd"
    
    # Ensure we don't overwrite the script itself if names match (though unlikely with .FCStd)
    # The prompt specifies the output must be next to the script.
    doc.saveAs(str(output_path))

if __name__ == "__main__":
    create_large_washer()
