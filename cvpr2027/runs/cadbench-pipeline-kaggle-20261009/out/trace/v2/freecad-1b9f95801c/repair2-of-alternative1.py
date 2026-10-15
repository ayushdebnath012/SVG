"""
FreeCAD 1.1 Script to generate a parametric Water Cup.
This script creates a single PartDesign Body with editable features 
based on the provided dimensions.
"""

from pathlib import Path
import FreeCAD as App
import Part
import Sketcher

def main():
    # Create a new document
    doc = App.newDocument("WaterCup")
    
    # Create the main Body
    body = doc.addObject("PartDesign::Body", "Body")
    body.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
    
    # Define Parameters (App::PropertyLength)
    params = body.newObject("App::VarSet", "Parameters")
    params.addProperty("App::PropertyLength", "cup_diameter", "Dimensions", "Outer diameter of the cup")
    params.addProperty("App::PropertyLength", "cup_height", "Dimensions", "Total height of the cup")
    params.addProperty("App::PropertyLength", "cup_thickness", "Dimensions", "Wall thickness")
    params.addProperty("App::PropertyLength", "inner_diameter", "Dimensions", "Calculated inner diameter")
    
    # Set initial values
    params.cup_diameter = 80.0
    params.cup_height = 120.0
    params.cup_thickness = 2.0
    
    # Helper to get parameter
    def get_param(name):
        return params.getPropertyByName(name)

    # --- Step 1: Create Outer Cylinder Sketch (Side View) ---
    # We will create the 3D shape by revolving a side-profile sketch.
    # The sketch plane is YZ (X=0). We draw a vertical line for height and 
    # a point at the outer radius.
    
    outer_sketch = body.newObject("Sketcher::SketchObject", "OuterSketch")
    outer_sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
    # In FreeCAD 1.1, Support is a list of tuples (Object, EdgeIndexList)
    # We use the YZ_Plane which is usually named "YZ_Plane" in the default document
    outer_sketch.Support = [(doc.getObject("YZ_Plane"), [])]
    
    # Add a line representing the height
    outer_sketch.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(0, params.cup_height, 0)), False)
    # Add a point at the outer radius (cup_diameter / 2)
    outer_radius = params.cup_diameter / 2.0
    outer_sketch.addGeometry(Part.LineSegment(App.Vector(0, params.cup_height, 0), App.Vector(0, params.cup_height, outer_radius)), False)
    outer_sketch.addGeometry(Part.LineSegment(App.Vector(0, params.cup_height, outer_radius), App.Vector(0, 0, outer_radius)), False)
    outer_sketch.addGeometry(Part.LineSegment(App.Vector(0, 0, outer_radius), App.Vector(0, 0, 0)), False)
    
    # Add constraints to define the shape fully
    outer_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 2), False) # Bottom point on origin
    outer_sketch.addConstraint(Sketcher.Constraint("DistanceY", 0, 1, 0, 1, params.cup_height), False) # Height
    outer_sketch.addConstraint(Sketcher.Constraint("DistanceZ", 0, 2, 0, 2, outer_radius), False) # Outer Radius
    outer_sketch.addConstraint(Sketcher.Constraint("Perpendicular", 0, 2, 0, 3), False) # Right angle
    
    # --- Step 2: Create Inner Cylinder Sketch (Side View) ---
    # Similar to outer, but using inner_diameter.
    inner_diameter = params.cup_diameter - 2.0 * params.cup_thickness
    inner_radius = inner_diameter / 2.0
    
    inner_sketch = body.newObject("Sketcher::SketchObject", "InnerSketch")
    inner_sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
    inner_sketch.Support = [(doc.getObject("YZ_Plane"), [])]
    
    # Add a line for the inner wall height (same as outer)
    inner_sketch.addGeometry(Part.LineSegment(App.Vector(0, 0, 0), App.Vector(0, params.cup_height, 0)), False)
    # Add point at inner radius
    inner_sketch.addGeometry(Part.LineSegment(App.Vector(0, params.cup_height, 0), App.Vector(0, params.cup_height, inner_radius)), False)
    inner_sketch.addGeometry(Part.LineSegment(App.Vector(0, params.cup_height, inner_radius), App.Vector(0, 0, inner_radius)), False)
    
    # Constraints
    inner_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 2), False)
    inner_sketch.addConstraint(Sketcher.Constraint("DistanceY", 0, 1, 0, 1, params.cup_height), False)
    inner_sketch.addConstraint(Sketcher.Constraint("DistanceZ", 0, 2, 0, 2, inner_radius), False)
    inner_sketch.addConstraint(Sketcher.Constraint("Perpendicular", 0, 2, 0, 3), False)
    
    # --- Step 3: Create Bottom Plate Sketch (Top View) ---
    # The cup has a bottom. We define the outer and inner circles for the bottom plate.
    bottom_sketch = body.newObject("Sketcher::SketchObject", "BottomSketch")
    bottom_sketch.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
    bottom_sketch.Support = [(doc.getObject("XY_Plane"), [])]
    
    # Outer circle
    bottom_sketch.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.cup_diameter / 2.0), False)
    # Inner circle (hole for the cup body)
    bottom_sketch.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), inner_radius), False)
    
    # Coaxial constraint
    bottom_sketch.addConstraint(Sketcher.Constraint("EqualRadius", 0, 1, 1, 2), False)
    
    # --- Step 4: Build the Body ---
    
    # 1. Pad the outer profile to full height
    pad_outer = body.newObject("PartDesign::Pad", "PadOuter")
    pad_outer.Profile = outer_sketch
    pad_outer.Length = params.cup_height
    pad_outer.Type = "Solid"
    
    # 2. Subtract the inner profile to create the hollow tube
    pocket_inner = body.newObject("PartDesign::Pocket", "PocketInner")
    pocket_inner.Profile = inner_sketch
    pocket_inner.Length = params.cup_height
    pocket_inner.Type = "ThroughAll"
    
    # 3. Add the bottom plate. 
    # We pad the bottom sketch. Since it contains two concentric circles, 
    # PartDesign will interpret this as a solid ring (washer) shape.
    pad_bottom = body.newObject("PartDesign::Pad", "PadBottom")
    pad_bottom.Profile = bottom_sketch
    pad_bottom.Length = 0 # 0 length acts as ThroughAll
    pad_bottom.Type = "Solid"
    
    # Recompute to ensure all features are calculated
    doc.recompute()
    
    # Determine output path based on __file__
    script_path = Path(__file__).resolve()
    output_path = script_path.with_name(script_path.stem + ".FCStd")
    
    # Save the document
    doc.saveAs(str(output_path))
    
    print(f"Model saved to: {output_path}")

if __name__ == "__main__":
    main()
