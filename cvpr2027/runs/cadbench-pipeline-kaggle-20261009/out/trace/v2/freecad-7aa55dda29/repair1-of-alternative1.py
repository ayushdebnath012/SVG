import os
import sys
from pathlib import Path
import FreeCAD as App
import Part
import Sketcher

def main():
    # Create a new document
    doc = App.newDocument("Washer_SquareNeck")

    # --- Parameters ---
    # Create a VarSet to hold parameters
    params = doc.addObject("App::VarSet", "Parameters")
    params.addProperty("App::PropertyLength", "washer_diameter", "Dimensions", "Outer diameter of the washer")
    params.washer_diameter = 60.0
    params.addProperty("App::PropertyLength", "washer_thickness", "Dimensions", "Thickness of the washer")
    params.washer_thickness = 10.0
    params.addProperty("App::PropertyLength", "square_neck_hole_width", "Dimensions", "Width of the central square hole")
    params.square_neck_hole_width = 20.0

    # --- Body ---
    body = doc.addObject("PartDesign::Body", "Body")
    body.Label = "Washer_Body"

    # --- Sketch 1: Washer Outer Profile ---
    # Sketch on XY plane at Z=0
    sketch_outer = body.newObject("Sketcher::SketchObject", "Sketch_Washer")
    # Correct Placement initialization for Sketcher::SketchObject
    sketch_outer.Placement = App.Placement(App.Vector(0, 0, 0))
    sketch_outer.ConstrainAuto = False
    sketch_outer.ConstrainLength = True
    
    # Add a circle for the outer diameter
    circle_geom = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.washer_diameter / 2.0)
    sketch_outer.addGeometry(circle_geom, False)

    # --- Sketch 2: Square Hole Profile ---
    # Sketch on XY plane at Z=0
    sketch_hole = body.newObject("Sketcher::SketchObject", "Sketch_Hole")
    sketch_hole.Placement = App.Placement(App.Vector(0, 0, 0))
    sketch_hole.ConstrainAuto = False
    sketch_hole.ConstrainLength = True

    # Define half-width for easier math
    half_width = params.square_neck_hole_width / 2.0
    
    # Vertices of the square: (h, h), (-h, h), (-h, -h), (h, -h)
    v1 = App.Vector(half_width, half_width, 0)
    v2 = App.Vector(-half_width, half_width, 0)
    v3 = App.Vector(-half_width, -half_width, 0)
    v4 = App.Vector(half_width, -half_width, 0)

    # Add lines connecting them
    sketch_hole.addGeometry(Part.LineSegment(v1, v2), False)
    sketch_hole.addGeometry(Part.LineSegment(v2, v3), False)
    sketch_hole.addGeometry(Part.LineSegment(v3, v4), False)
    sketch_hole.addGeometry(Part.LineSegment(v4, v1), False)

    # --- Feature: Pad (The Washer Body) ---
    pad = body.newObject("PartDesign::Pad", "Pad_Washer")
    pad.Profile = sketch_outer
    pad.Length = params.washer_thickness
    pad.Type = "FullyRigid"
    pad.MidPlane = False

    # --- Feature: Pocket (The Square Hole) ---
    pocket = body.newObject("PartDesign::Pocket", "Pocket_Hole")
    pocket.Profile = sketch_hole
    pocket.Type = "ThroughAll" # Cuts all the way through
    pocket.Clean = True

    # --- Finalization ---
    # Ensure everything is recomputed
    doc.recompute()

    # Save the document to the specific path derived from __file__
    script_path = Path(__file__).resolve()
    output_path = script_path.with_suffix(".FCStd")

    # Save the file
    doc.saveAs(str(output_path))
    
    print(f"Model saved to: {output_path}")

if __name__ == "__main__":
    main()
