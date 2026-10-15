from pathlib import Path
import FreeCAD as App
import Part
import Sketcher

def create_flange():
    # Initialize Document
    doc = App.newDocument("Flange")
    
    # Create a Body
    body = doc.addObject("PartDesign::Body", "Body")
    body.Placement = App.Placement(App.Vector(0, 0, 0))

    # 1. Define Parameters
    params = body.newObject("App::Parameter", "Parameters")
    params.addProperty("App::PropertyLength", "outer_diameter", "Dimensions", "Outer diameter of the flange")
    params.outer_diameter = 125.4125
    
    params.addProperty("App::PropertyLength", "flange_thickness", "Dimensions", "Thickness of the flange")
    params.flange_thickness = 23.01875
    
    params.addProperty("App::PropertyLength", "bore_diameter", "Dimensions", "Diameter of the central bore")
    params.bore_diameter = 28.971875
    
    params.addProperty("App::PropertyLength", "bolt_circle_diameter", "Dimensions", "Diameter of the bolt circle")
    params.bolt_circle_diameter = 103.1875
    
    params.addProperty("App::PropertyLength", "mounting_hole_diameter", "Dimensions", "Diameter of mounting holes")
    params.mounting_hole_diameter = 13.49375
    
    params.addProperty("App::PropertyInteger", "number_of_mounting_holes", "Dimensions", "Count of mounting holes")
    params.number_of_mounting_holes = 4

    # 2. Base Sketch (Flange Outer Profile and Central Bore)
    # Use XY plane as default origin
    base_sketch = body.newObject("Sketcher::SketchObject", "BaseSketch")
    base_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
    base_sketch.BaseConstraints = True
    base_sketch.ConstrainToPlane = "XY_Plane"
    base_sketch.ConstrainToAxis = "X_Axis"
    
    # Add Outer Circle
    outer_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.outer_diameter / 2.0)
    base_sketch.addGeometry(outer_circle, False)
    
    # Add Central Bore Circle (Same center, smaller radius)
    bore_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.bore_diameter / 2.0)
    base_sketch.addGeometry(bore_circle, False)
    
    # Add a point at the origin to help with constraints if needed, 
    # though starting both circles at (0,0,0) usually suffices for concentricity in simple cases.
    origin_point = Part.Point(App.Vector(0, 0, 0))
    base_sketch.addGeometry(origin_point, False)
    
    # Add coincident constraints: Point (index 2) coincident with Center of Outer (index 0) and Center of Bore (index 1)
    # Syntax: Constraint("Coincident", <geo_idx>, <sub_idx>, <geo_idx2>, <sub_idx2>)
    # For circles, sub_idx 0 is center, sub_idx 1 is geometry. For Point, sub_idx 0 is the point.
    try:
        base_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 0, 2, 0)) # Outer center to Point
        base_sketch.addConstraint(Sketcher.Constraint("Coincident", 1, 0, 2, 0)) # Bore center to Point
    except Exception as e:
        print(f"Warning during constraint addition: {e}")

    # 3. Pad Feature (Main Flange Plate)
    pad = body.newObject("PartDesign::Pad", "FlangePad")
    pad.Profile = base_sketch
    pad.Length = params.flange_thickness
    pad.Type = "Blind"
    
    # 4. Central Through Bore
    # Create a sketch for the hole on the top face of the pad
    bore_sketch = body.newObject("Sketcher::SketchObject", "BoreSketch")
    bore_sketch.Placement = App.Placement(App.Vector(0, 0, params.flange_thickness))
    bore_sketch.BaseConstraints = True
    bore_sketch.ConstrainToPlane = "XY_Plane"
    
    # Add Bore Circle again
    bore_sketch.addGeometry(bore_circle, False)
    
    pocket = body.newObject("PartDesign::Pocket", "CentralBore")
    pocket.Profile = bore_sketch
    pocket.Type = "ThroughAll"
    
    # 5. Mounting Holes
    # Calculate positions
    bolt_radius = params.bolt_circle_diameter / 2.0
    hole_radius = params.mounting_hole_diameter / 2.0
    
    # Create a sketch for one hole, then pattern it
    # We place the sketch on the top face of the flange (Z = flange_thickness)
    hole_sketch = body.newObject("Sketcher::SketchObject", "MountingHoleSketch")
    hole_sketch.Placement = App.Placement(App.Vector(0, 0, params.flange_thickness))
    hole_sketch.BaseConstraints = True
    hole_sketch.ConstrainToPlane = "XY_Plane"
    
    # Add a point at the center of the bolt circle (Z=thickness)
    bolt_center = Part.Point(App.Vector(bolt_radius, 0, 0))
    hole_sketch.addGeometry(bolt_center, False)
    
    # Add the hole circle
    hole_circle = Part.Circle(bolt_center, App.Vector(0, 0, 1), hole_radius)
    hole_sketch.addGeometry(hole_circle, False)
    
    # Add constraints: Coincident center of hole with bolt_center point
    try:
        hole_sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 0, 1, 0))
    except Exception as e:
        print(f"Warning during hole constraint addition: {e}")

    hole_pocket = body.newObject("PartDesign::Pocket", "SingleMountingHole")
    hole_pocket.Profile = hole_sketch
    hole_pocket.Type = "ThroughAll"
    
    # Pattern the hole
    # Polar Pattern
    pattern = body.newObject("PartDesign::PolarPattern", "MountingHolesPattern")
    pattern.Originals = [hole_pocket]
    pattern.Axis = (doc.getObject("Z_Axis"), [""]) 
    pattern.Angle = 360.0
    pattern.Occurrences = params.number_of_mounting_holes
    
    # 6. Fillets (Optional but good practice)
    # Fillet the outer edge of the flange
    # We need to select the edge from the Pad. 
    # In headless mode, selecting edges by index is unreliable without a helper.
    # However, we can try to fillet the top face outer edge if we can identify it.
    # Given the complexity and potential for failure in headless edge selection, 
    # we will rely on the core geometry being correct as per the prompt's emphasis on 
    # "named document objects" and "parametric feature tree".
    
    # Recompute everything
    doc.recompute()
    
    # Save
    script_path = Path(__file__).resolve()
    output_path = script_path.with_suffix(".FCStd")
    
    # Ensure the path exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    doc.saveAs(str(output_path))
    
    # Clean up doc to prevent warnings in some environments
    App.removeObject(doc.Name)

if __name__ == "__main__":
    create_flange()
