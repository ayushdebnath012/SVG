from pathlib import Path
import FreeCAD as App
import Part
import Sketcher
import math

def main():
    # 1. Initialize Document
    doc = App.newDocument("SplineShaft")
    
    # 2. Define Named Parameters using App::VarSet (the correct type for named parameters in PartDesign)
    params = doc.addObject("App::VarSet", "Parameters")
    params.addProperty("App::PropertyLength", "shaft_spline_height", "Dimensions", "Spline height")
    params.addProperty("App::PropertyLength", "shaft_diameter", "Dimensions", "Smooth shaft diameter")
    params.addProperty("App::PropertyLength", "shaft_length", "Dimensions", "Smooth shaft length")
    params.addProperty("App::PropertyLength", "shaft_spline_module", "Dimensions", "Spline module")
    params.addProperty("App::PropertyLength", "shaft_spline_pitch_diameter", "Dimensions", "Spline pitch diameter")
    params.addProperty("App::PropertyInteger", "shaft_number_teeth", "Dimensions", "Number of teeth")
    params.addProperty("App::PropertyAngle", "shaft_pressure_angle", "Dimensions", "Pressure angle (degrees)")
    
    # Set default values based on prompt
    params.shaft_spline_height = 10.0
    params.shaft_diameter = 24.0
    params.shaft_length = 20.0
    params.shaft_spline_module = 2.0
    params.shaft_spline_pitch_diameter = 30.0 # 15 * 2
    params.shaft_number_teeth = 15
    params.shaft_pressure_angle = 30.0
    
    # 3. Create PartDesign Body
    body = doc.addObject("PartDesign::Body", "Body")
    body.Placement = App.Placement(App.Vector(0, 0, 0))
    
    # 4. Create Base Sketch (Spline Profile)
    base_sketch = body.newObject("Sketcher::SketchObject", "SplineSketch")
    base_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
    base_sketch.Placement = App.Placement(App.RotationZ(0))
    base_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
    base_sketch.AttachmentSupport = (doc.getObject("XY_Plane"), [""])
    base_sketch.MapMode = "FlatFace"
    base_sketch.ConstraintFixToPlane = (doc.getObject("XY_Plane"), [""])
    base_sketch.Technology = "ISO"
    
    # Generate Spline Curve in Part space
    spline_curve = Part.Spline()
    
    pitch_r = params.shaft_spline_pitch_diameter / 2.0
    inner_r = pitch_r - params.shaft_spline_height
    outer_r = pitch_r
    
    num_points = 100 # High resolution for smooth spline
    for i in range(num_points):
        angle = 2 * math.pi * i / num_points
        # Frequency multiplier for number of teeth
        freq = params.shaft_number_teeth
        # Radius oscillates between inner_r and outer_r
        r_val = inner_r + (outer_r - inner_r) * (1 + math.cos(freq * angle)) / 2.0
        
        pt = App.Vector(r_val * math.cos(angle), r_val * math.sin(angle), 0)
        spline_curve.addPoint(pt)
    
    spline_curve.close()
    
    # Add the spline curve to the sketch
    base_sketch.addGeometry(spline_curve, False)
    
    # Add a dummy line at origin to constrain to
    origin_line = Part.LineSegment(App.Vector(0, 0, 0), App.Vector(0.001, 0, 0))
    base_sketch.addGeometry(origin_line, False)
    
    # Constrain the spline to be centered at the origin.
    # We constrain the start and end of the spline to the start and end of the origin line.
    idx_spline = len(base_sketch.Geometry) - 1
    idx_origin = len(base_sketch.Geometry) - 2
    
    # Constrain spline start to origin line start
    base_sketch.addConstraint(Sketcher.Constraint("Coincident", idx_spline, 0, idx_origin, 0))
    # Constrain spline end to origin line end
    base_sketch.addConstraint(Sketcher.Constraint("Coincident", idx_spline, 1, idx_origin, 1))
    
    # 5. Create Pad for the Spline Section
    pad_spline = body.newObject("PartDesign::Pad", "PadSpline")
    pad_spline.Profile = base_sketch
    pad_spline.Length = params.shaft_spline_height
    pad_spline.Midplane = False
    pad_spline.Reversed = False
    
    # 6. Create Pocket for the Smooth Shaft Section
    # We need a sketch for the smooth shaft.
    smooth_sketch = body.newObject("Sketcher::SketchObject", "SmoothShaftSketch")
    smooth_sketch.Placement = App.Placement(App.Vector(0, 0, params.shaft_spline_height))
    smooth_sketch.Placement = App.Placement(App.RotationZ(0))
    smooth_sketch.Placement = App.Placement(App.Vector(0, 0, params.shaft_spline_height))
    smooth_sketch.AttachmentSupport = (doc.getObject("XY_Plane"), [""])
    smooth_sketch.MapMode = "FlatFace"
    smooth_sketch.ConstraintFixToPlane = (doc.getObject("XY_Plane"), [""])
    smooth_sketch.Technology = "ISO"
    
    # Add a circle for the smooth shaft
    smooth_radius = params.shaft_diameter / 2.0
    smooth_circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), smooth_radius)
    smooth_sketch.addGeometry(smooth_circle, False)
    
    # Add a dummy line at origin to constrain to
    origin_line_smooth = Part.LineSegment(App.Vector(0, 0, 0), App.Vector(0.001, 0, 0))
    smooth_sketch.addGeometry(origin_line_smooth, False)
    
    idx_smooth_circle = len(smooth_sketch.Geometry) - 1
    idx_origin_smooth = len(smooth_sketch.Geometry) - 2
    
    # Constrain circle center to origin line start
    smooth_sketch.addConstraint(Sketcher.Constraint("Coincident", idx_smooth_circle, 0, idx_origin_smooth, 0))
    # Constrain circle center to origin line end (same point)
    smooth_sketch.addConstraint(Sketcher.Constraint("Coincident", idx_smooth_circle, 0, idx_origin_smooth, 1))
    
    # Create Pocket for the smooth shaft
    pocket_smooth = body.newObject("PartDesign::Pocket", "PocketSmooth")
    pocket_smooth.Profile = smooth_sketch
    pocket_smooth.Length = params.shaft_length
    pocket_smooth.Type = "Blind"
    pocket_smooth.Midplane = False
    pocket_smooth.Reversed = False
    
    # 7. Recompute
    doc.recompute()
    
    # 8. Save the file
    script_path = Path(__file__).resolve()
    output_path = script_path.with_suffix(".FCStd")
    
    doc.saveAs(str(output_path))
    print(f"Model saved to: {output_path}")

if __name__ == "__main__":
    main()
