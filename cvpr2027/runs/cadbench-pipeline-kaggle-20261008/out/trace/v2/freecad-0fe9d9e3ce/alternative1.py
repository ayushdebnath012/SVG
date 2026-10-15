"""
FreeCAD 1.1 Script to generate a parametric mounting flange.
Generates: /app/answer.FCStd (derived from __file__).
"""

from pathlib import Path
import FreeCAD as App
import Part
import Sketcher
import math

def main():
    # 1. Create Document
    doc = App.newDocument("MountingFlange")
    
    # Define Parameters
    params = doc.addObject("App::PropertyGroupProxy", "Parameters")
    params.Name = "Parameters"
    params.addProperty("App::PropertyLength", "inner_diameter", "Parameters", "central hole")
    params.inner_diameter = 34.925
    params.addProperty("App::PropertyLength", "outer_diameter", "Parameters", "flange outer")
    params.outer_diameter = 69.454
    params.addProperty("App::PropertyLength", "flange_thickness", "Parameters", "thickness")
    params.flange_thickness = 13.097
    params.addProperty("App::PropertyLength", "pitch_circle_diameter", "Parameters", "bolt circle")
    params.pitch_circle_diameter = 56.356
    params.addProperty("App::PropertyLength", "bolt_hole_diameter", "Parameters", "bolt hole")
    params.bolt_hole_diameter = 6.747
    params.addProperty("App::PropertyInteger", "number_bolt_holes", "Parameters", "count")
    params.number_bolt_holes = 4

    # Create Body
    body = doc.addObject("PartDesign::Body", "Body")
    doc.addObject("App::DocumentObjectGroup", "BodyGroup")
    BodyGroup = doc.addObject("App::DocumentObjectGroup", "BodyGroup")
    BodyGroup.Name = "BodyGroup"
    doc.addObject(App.getDocumentObjectType("App::DocumentObjectGroup"), "BodyGroup") # Ensure it's added
    
    # Actually, simpler way to attach to body in headless:
    # Just create the body and add objects to doc, they belong to body implicitly if created via body.newObject
    # But standard newDocument creates an empty root. We need to put the body in the doc.
    
    # Let's restart the object creation flow to ensure correct hierarchy
    doc.removeObject("Parameters")
    doc.removeObject("Body")
    
    params = doc.addObject("App::PropertyGroupProxy", "Parameters")
    params.addProperty("App::PropertyLength", "inner_diameter", "Parameters", "central hole")
    params.inner_diameter = 34.925
    params.addProperty("App::PropertyLength", "outer_diameter", "Parameters", "flange outer")
    params.outer_diameter = 69.454
    params.addProperty("App::PropertyLength", "flange_thickness", "Parameters", "thickness")
    params.flange_thickness = 13.097
    params.addProperty("App::PropertyLength", "pitch_circle_diameter", "Parameters", "bolt circle")
    params.pitch_circle_diameter = 56.356
    params.addProperty("App::PropertyLength", "bolt_hole_diameter", "Parameters", "bolt hole")
    params.bolt_hole_diameter = 6.747
    params.addProperty("App::PropertyInteger", "number_bolt_holes", "Parameters", "count")
    params.number_bolt_holes = 4
    
    body = doc.addObject("PartDesign::Body", "Body")
    
    # 2. Create Main Flange Sketch (Profile)
    # Plane: XY
    sketch_main = body.newObject("Sketcher::SketchObject", "SketchMain")
    sketch_main.Plane = "XY_Plane"
    sketch_main.ConstrainAuto = False
    
    # Outer Circle
    outer_circle = sketch_main.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.outer_diameter / 2.0), False)
    outer_circle.setExpression("Radius", "Parameters.outer_diameter/2")
    
    # Inner Hole (for reference in the pocket)
    inner_circle = sketch_main.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.inner_diameter / 2.0), False)
    inner_circle.setExpression("Radius", "Parameters.inner_diameter/2")
    
    # 3. Create Central Hole Pocket Sketch
    # We can reuse the inner circle geometry or create a specific sketch for clarity.
    # Let's create a specific sketch for the pocket to be explicit.
    sketch_pocket = body.newObject("Sketcher::SketchObject", "SketchPocket")
    sketch_pocket.Plane = "XY_Plane"
    
    # Reuse the circle geometry by referencing the sketch object or just adding a new circle
    # In FreeCAD PartDesign, a Pocket takes a Sketch object as Profile.
    # We can add the circle directly to the pocket sketch.
    pocket_circle = sketch_pocket.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.inner_diameter / 2.0), False)
    pocket_circle.setExpression("Radius", "Parameters.inner_diameter/2")
    
    # 4. Create Bolt Hole Sketch
    sketch_bolt = body.newObject("Sketcher::SketchObject", "SketchBolt")
    sketch_bolt.Plane = "XY_Plane"
    
    bolt_circle_geom = sketch_bolt.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.pitch_circle_diameter / 2.0), False)
    bolt_circle_geom.setExpression("Radius", "Parameters.pitch_circle_diameter/2")
    
    bolt_hole_geom = sketch_bolt.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.bolt_hole_diameter / 2.0), False)
    bolt_hole_geom.setExpression("Radius", "Parameters.bolt_hole_diameter/2")
    
    # 5. Pad Feature (Flange Body)
    pad = body.newObject("PartDesign::Pad", "PadFlange")
    pad.Profile = sketch_main
    pad.Length = params.flange_thickness
    pad.MidPlane = False # Build upwards from XY plane
    pad.setExpression("Length", "Parameters.flange_thickness")
    
    # 6. Pocket Feature (Central Hole)
    pocket = body.newObject("PartDesign::Pocket", "PocketCenter")
    pocket.Profile = sketch_pocket
    pocket.Type = "ThroughAll"
    
    # 7. Bolt Holes (Pattern)
    # We need to define the geometry first in a sketch, then pattern it.
    # However, PartDesign::Hole feature is often easier if we define the hole geometry in a sketch 
    # and use a Polar Pattern on the Hole feature.
    
    # Create a sketch with the hole geometry and the reference circle
    sketch_bolt_pattern = body.newObject("Sketcher::SketchObject", "SketchBoltPattern")
    sketch_bolt_pattern.Plane = "XY_Plane"
    
    # Reference Circle (Pitch Circle)
    ref_circle = sketch_bolt_pattern.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.pitch_circle_diameter / 2.0), False)
    ref_circle.setExpression("Radius", "Parameters.pitch_circle_diameter/2")
    
    # Hole Circle (offset 0 for now, will be constrained or positioned)
    # Actually, for a pattern of holes, we usually sketch one hole at the origin and pattern it around a circle.
    hole_geom = sketch_bolt_pattern.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.bolt_hole_diameter / 2.0), False)
    hole_geom.setExpression("Radius", "Parameters.bolt_hole_diameter/2")
    
    # Add constraints: Hole center coincident with Pitch Circle center (already true by default vector 0,0)
    # We need to ensure the hole is concentric with the pitch circle initially so the pattern distributes it correctly.
    
    # Create the Hole Feature
    bolt_hole = body.newObject("PartDesign::Hole", "HoleBolt")
    bolt_hole.Profile = sketch_bolt_pattern
    bolt_hole.Type = "Simple"
    bolt_hole.Angle = 90.0 # Blind hole depth or ThroughAll? 
    # The prompt implies a mounting flange, usually holes are through.
    bolt_hole.Type = "Simple" 
    # Actually, for a through hole, we can use Length = -1e10 or Type="ThroughAll" in newer versions, 
    # but "Simple" with a huge length or "ThroughAll" is better. Let's use ThroughAll logic or large negative.
    # In PartDesign::Hole, Type="Simple", Length can be negative for through.
    bolt_hole.Length = -1000.0
    bolt_hole.SetExpression("Length", "-1000") # Ensure it's treated as through
    
    # Pattern the Hole Feature
    pattern = body.newObject("PartDesign::PolarPattern", "PatternBolts")
    pattern.Originals = [bolt_hole]
    pattern.Axis = (doc.getObject("Z_Axis"), [""])
    pattern.AxisAngle = 0
    pattern.Occurrences = params.number_bolt_holes
    # Calculate angle step
    angle_step = 360.0 / params.number_bolt_holes
    pattern.setExpression("Angle", "360/Parameters.number_bolt_holes")
    pattern.setExpression("Occurrences", "Parameters.number_bolt_holes")
    
    # 8. Fillet/Chamfer (Optional, but good for flanges usually. Prompt didn't strictly require it, 
    # but "round mounting flange" often implies a fillet on the inner corner of the center hole or outer rim.
    # Let's add a small fillet to the inner corner of the flange for a nicer look, or just stick to the strict geometry.
    # The prompt asks to "reproduce the part described". Description: "circular flange body with a central plain through hole and a set of bolt holes".
    # No specific fillet requested. I will skip fillet to match description exactly.)

    # Finalize
    doc.recompute()
    
    # Save
    output_path = Path(__file__).resolve().parent / "answer.FCStd"
    doc.save(str(output_path))

if __name__ == "__main__":
    main()
