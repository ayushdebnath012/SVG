from pathlib import Path
import FreeCAD as App
import Part
import Sketcher

def main():
    # Create new document
    doc = App.newDocument("FlangeMounting")

    # 1. Create named parameters to drive the geometry
    # Using App::VarSet as per the reference pattern for named, editable parameters
    param_obj = doc.addObject("App::VarSet", "Parameters")
    param_obj.addProperty("App::PropertyLength", "inner_diameter", "Dimensions", "Inner bore diameter")
    param_obj.addProperty("App::PropertyLength", "outer_diameter", "Dimensions", "Outer flange diameter")
    param_obj.addProperty("App::PropertyLength", "flange_thickness", "Dimensions", "Thickness of flange")
    param_obj.addProperty("App::PropertyLength", "pitch_circle_diameter", "Dimensions", "Bolt circle diameter")
    param_obj.addProperty("App::PropertyLength", "bolt_hole_diameter", "Dimensions", "Diameter of bolt holes")
    param_obj.addProperty("App::PropertyInteger", "number_bolt_holes", "Dimensions", "Count of bolt holes")

    # Set initial values from the prompt
    param_obj.inner_diameter = 34.925
    param_obj.outer_diameter = 69.454
    param_obj.flange_thickness = 26.194
    param_obj.pitch_circle_diameter = 57.547
    param_obj.bolt_hole_diameter = 6.747
    param_obj.number_bolt_holes = 4

    # 2. Create the Body
    body = doc.addObject("PartDesign::Body", "Body")

    # 3. Create Reference Plane (XY_Plane)
    # In headless mode, we create a Plane object to serve as the sketch support
    ref_plane = doc.addObject("Part::Plane", "XY_Plane")
    ref_plane.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())

    # 4. Create Main Profile Sketch (Outer Diameter)
    sketch_main = doc.addObject("Sketcher::SketchObject", "Sketch_Main")
    # In FreeCAD 1.1, the property is 'Placement' for the sketch object itself to define its position/orientation.
    # The 'Support' property is used to attach the sketch to a face/plane.
    # However, the error indicated 'Support' is missing. 
    # In FreeCAD 1.1, Sketcher::SketchObject uses 'Placement' to define the sketch plane and offset.
    # We set the Placement to be on the XY plane (Z=0).
    sketch_main.Placement = App.Placement(App.Vector(0, 0, 0), App.Rotation())
    
    # Add Circle for Outer Diameter
    r_outer = param_obj.outer_diameter / 2.0
    circle_outer = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r_outer)
    sketch_main.addGeometry(circle_outer, False)

    # 5. Create Central Bore Sketch
    # We create a second sketch on the same plane (slightly offset Z to avoid coplanar issues if necessary, 
    # though FlatFace usually handles it, but distinct sketches are safer for feature separation).
    sketch_hole = doc.addObject("Sketcher::SketchObject", "Sketch_Hole")
    sketch_hole.Placement = App.Placement(App.Vector(0, 0, 0.001), App.Rotation())
    
    r_inner = param_obj.inner_diameter / 2.0
    circle_inner = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r_inner)
    sketch_hole.addGeometry(circle_inner, False)

    # 6. Create Bolt Hole Sketch
    sketch_bolt = doc.addObject("Sketcher::SketchObject", "Sketch_Bolt")
    sketch_bolt.Placement = App.Placement(App.Vector(0, 0, 0.002), App.Rotation())
    
    r_bolt = param_obj.bolt_hole_diameter / 2.0
    circle_bolt = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), r_bolt)
    sketch_bolt.addGeometry(circle_bolt, False)

    # 7. Create PartDesign Features
    
    # Feature 1: Pad (The Flange Body)
    pad = body.newObject("PartDesign::Pad", "Pad_Flange")
    pad.Profile = sketch_main
    pad.Length = param_obj.flange_thickness
    pad.Type = "Full"

    # Feature 2: Pocket (The Central Bore)
    pocket_center = body.newObject("PartDesign::Pocket", "Pocket_Center")
    pocket_center.Profile = sketch_hole
    pocket_center.Type = "ThroughAll"

    # Feature 3: Pocket (Single Bolt Hole)
    pocket_bolt = body.newObject("PartDesign::Pocket", "Pocket_Bolt_Single")
    pocket_bolt.Profile = sketch_bolt
    pocket_bolt.Type = "ThroughAll"

    # Feature 4: Polar Pattern for Bolt Holes
    # Create an Axis object for the pattern
    axis_obj = doc.addObject("Part::Axis", "Pattern_Axis")
    # Set Point and Axis vector
    try:
        axis_obj.Point = App.Vector(0, 0, 0)
        axis_obj.Axis = App.Vector(0, 0, 1)
    except AttributeError:
        # Fallback if properties differ
        pass

    pattern = body.newObject("PartDesign::PolarPattern", "Pattern_Bolts")
    pattern.Originals = [pocket_bolt]
    pattern.Axis = (axis_obj, [""])
    pattern.NumberOfOccurrences = param_obj.number_bolt_holes
    angle_step = 360.0 / param_obj.number_bolt_holes
    pattern.Angle = angle_step

    # 8. Finalize
    doc.recompute()

    # 9. Save
    script_path = Path(__file__).resolve()
    output_path = script_path.parent / f"{script_path.stem}.FCStd"
    
    doc.saveAs(str(output_path))

if __name__ == "__main__":
    main()
