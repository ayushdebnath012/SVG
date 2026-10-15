from pathlib import Path
import FreeCAD as App
import Part
import Sketcher
import math

def main():
    # 1. Initialize Document
    doc = App.newDocument("SplineShaft")
    
    # 2. Define Named Parameters (App::Parameter)
    params = doc.addObject("App::Parameter", "Parameters")
    params.Name = "Parameters"
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
    
    # Constrain the spline to be centered at the origin.
    # We add a dummy point at (0,0) and constrain it to the spline start.
    # Since we can't easily add a point geometry, we add a tiny line segment at origin and constrain it.
    origin_line = Part.LineSegment(App.Vector(0, 0, 0), App.Vector(0.001, 0, 0))
    base_sketch.addGeometry(origin_line, False)
    
    # Constrain the start of the spline to the start of the origin line (which is at 0,0)
    # We need to get the indices. The spline is the last added geometry, origin_line is the new one.
    # However, indices are dynamic. Let's use the geometry objects directly if possible, 
    # but Sketcher constraints usually use indices.
    # Let's rely on the fact that the spline is generated from (0,0) outwards.
    # We need to fix the rotation. Let's constrain the tangent at the start to be horizontal?
    # Or simpler: Constrain the start point of the spline to the origin line start.
    # In FreeCAD 1.1, we can reference geometries by index.
    # Spline is index -1 (last added), OriginLine is index -2.
    # But let's be safe and add a constraint on the spline start point to the origin.
    # We can add a "Point" constraint? No.
    # Let's add a constraint "Coincident" between the spline start and the origin line start.
    # Index of spline: len(base_sketch.Geometry) - 1
    # Index of origin line: len(base_sketch.Geometry) - 2
    
    # Actually, a more robust way in FreeCAD 1.1 is to add a constraint "Horizontal" on the spline start?
    # No, let's just add a constraint "Coincident" between the spline start and the origin line start.
    # We need to ensure the spline is closed and centered.
    # Let's add a constraint "Coincident" between the spline start and the origin line start.
    # And "Coincident" between the spline end and the origin line end?
    # Since the spline is closed, start == end.
    # Let's just constrain the start of the spline to the origin line start.
    
    # To make it robust, let's add a constraint "Coincident" between the spline start and the origin line start.
    # And "Coincident" between the spline end and the origin line end.
    # This ensures the spline is centered at (0,0).
    
    # Note: In FreeCAD 1.1, the constraint syntax is:
    # Sketcher.Constraint("Coincident", index1, point1, index2, point2)
    # point1 and point2 are 0 (start) or 1 (end).
    
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
    
    # Constrain the circle to be centered at the origin of the sketch plane
    # The sketch is placed at (0,0, shaft_spline_height). The circle is at (0,0,0) in local coords.
    # We need to constrain the circle center to the origin of the sketch plane.
    # Add a point at (0,0) and constrain it?
    # Or use the "Center" constraint on the circle?
    # In Sketcher, we can add a constraint "Center" on the circle?
    # No, we need to constrain the circle center to the origin.
    # Let's add a point at (0,0) using a LineSegment from (0,0) to (0,0)? No.
    # Let's add a constraint "Horizontal" and "Vertical" on the circle center?
    # Or better: Add a constraint "Coincident" between the circle center and a point at (0,0).
    # Let's add a dummy line at (0,0) and constrain it.
    
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
