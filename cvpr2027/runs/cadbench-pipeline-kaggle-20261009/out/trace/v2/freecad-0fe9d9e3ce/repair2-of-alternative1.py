"""
FreeCAD 1.1 Script to generate a parametric mounting flange.
Generates: /app/answer.FCStd (derived from __file__).
"""

from pathlib import Path
import FreeCAD as App
import Part
import Sketcher

def main():
    # 1. Create Document
    doc = App.newDocument("MountingFlange")
    
    # Define Parameters using App::PropertyGroupProxy as a container for variables
    # In FreeCAD 1.1, we create a GroupProxy and add properties to it.
    params_group = doc.addObject("App::PropertyGroupProxy", "Parameters")
    params_group.addProperty("App::PropertyLength", "inner_diameter", "Parameters", "central hole")
    params_group.inner_diameter = 34.925
    params_group.addProperty("App::PropertyLength", "outer_diameter", "Parameters", "flange outer")
    params_group.outer_diameter = 69.454
    params_group.addProperty("App::PropertyLength", "flange_thickness", "Parameters", "thickness")
    params_group.flange_thickness = 13.097
    params_group.addProperty("App::PropertyLength", "pitch_circle_diameter", "Parameters", "bolt circle")
    params_group.pitch_circle_diameter = 56.356
    params_group.addProperty("App::PropertyLength", "bolt_hole_diameter", "Parameters", "bolt hole")
    params_group.bolt_hole_diameter = 6.747
    params_group.addProperty("App::PropertyInteger", "number_bolt_holes", "Parameters", "count")
    params_group.number_bolt_holes = 4

    # Create Body
    body = doc.addObject("PartDesign::Body", "Body")
    
    # 2. Create Main Flange Sketch (Profile)
    # Plane: XY
    sketch_main = body.newObject("Sketcher::SketchObject", "SketchMain")
    sketch_main.Plane = "XY_Plane"
    sketch_main.ConstrainAuto = False
    
    # Outer Circle
    outer_circle = sketch_main.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params_group.outer_diameter / 2.0), False)
    outer_circle.setExpression("Radius", "Parameters.outer_diameter/2")
    
    # Inner Hole (for reference in the pocket)
    inner_circle = sketch_main.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params_group.inner_diameter / 2.0), False)
    inner_circle.setExpression("Radius", "Parameters.inner_diameter/2")
    
    # 3. Create Central Hole Pocket Sketch
    sketch_pocket = body.newObject("Sketcher::SketchObject", "SketchPocket")
    sketch_pocket.Plane = "XY_Plane"
    
    # Add the circle for the pocket
    pocket_circle = sketch_pocket.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params_group.inner_diameter / 2.0), False)
    pocket_circle.setExpression("Radius", "Parameters.inner_diameter/2")
    
    # 4. Create Bolt Hole Sketch
    sketch_bolt = body.newObject("Sketcher::SketchObject", "SketchBolt")
    sketch_bolt.Plane = "XY_Plane"
    
    # Reference Circle (Pitch Circle)
    ref_circle = sketch_bolt.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params_group.pitch_circle_diameter / 2.0), False)
    ref_circle.setExpression("Radius", "Parameters.pitch_circle_diameter/2")
    
    # Hole Circle
    hole_geom = sketch_bolt.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params_group.bolt_hole_diameter / 2.0), False)
    hole_geom.setExpression("Radius", "Parameters.bolt_hole_diameter/2")
    
    # 5. Pad Feature (Flange Body)
    pad = body.newObject("PartDesign::Pad", "PadFlange")
    pad.Profile = sketch_main
    pad.Length = params_group.flange_thickness
    pad.MidPlane = False
    pad.setExpression("Length", "Parameters.flange_thickness")
    
    # 6. Pocket Feature (Central Hole)
    pocket = body.newObject("PartDesign::Pocket", "PocketCenter")
    pocket.Profile = sketch_pocket
    pocket.Type = "ThroughAll"
    
    # 7. Bolt Holes (Pattern)
    # Create a sketch with the hole geometry and the reference circle
    sketch_bolt_pattern = body.newObject("Sketcher::SketchObject", "SketchBoltPattern")
    sketch_bolt_pattern.Plane = "XY_Plane"
    
    # Reference Circle (Pitch Circle)
    ref_circle_pat = sketch_bolt_pattern.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params_group.pitch_circle_diameter / 2.0), False)
    ref_circle_pat.setExpression("Radius", "Parameters.pitch_circle_diameter/2")
    
    # Hole Circle (at origin)
    hole_geom_pat = sketch_bolt_pattern.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params_group.bolt_hole_diameter / 2.0), False)
    hole_geom_pat.setExpression("Radius", "Parameters.bolt_hole_diameter/2")
    
    # Create the Hole Feature
    bolt_hole = body.newObject("PartDesign::Hole", "HoleBolt")
    bolt_hole.Profile = sketch_bolt_pattern
    bolt_hole.Type = "Simple"
    # Use a very large negative length to simulate ThroughAll for holes
    bolt_hole.Length = -1000.0
    bolt_hole.setExpression("Length", "-1000")
    
    # Pattern the Hole Feature
    pattern = body.newObject("PartDesign::PolarPattern", "PatternBolts")
    pattern.Originals = [bolt_hole]
    pattern.Axis = (doc.getObject("Z_Axis"), [""])
    pattern.Occurrences = params_group.number_bolt_holes
    # Calculate angle step
    angle_step = 360.0 / params_group.number_bolt_holes
    pattern.setExpression("Angle", "360/Parameters.number_bolt_holes")
    pattern.setExpression("Occurrences", "Parameters.number_bolt_holes")
    
    # Finalize
    doc.recompute()
    
    # Save
    # Derive path from __file__
    script_path = Path(__file__).resolve()
    output_path = script_path.parent / "answer.FCStd"
    
    doc.save(str(output_path))

if __name__ == "__main__":
    main()
