import FreeCAD as App
import Part
from pathlib import Path
import Sketcher
import math

# --- Configuration ---
# Derived from task requirements
params = {
    "handle_length": 110.0,
    "handle_diameter": 28.0,
    "cross_flat_width": 80.0,
    "hex_height": 30.0
}

# --- Document Setup ---
doc = App.newDocument("Dumbbell")

# Create Body
body = doc.addObject("PartDesign::Body", "Body")
doc.setActiveObject("Body")

# Add Parameters to the Body object
body.addProperty("App::PropertyLength", "handle_length")
body.handle_length = params["handle_length"]
body.addProperty("App::PropertyLength", "handle_diameter")
body.handle_diameter = params["handle_diameter"]
body.addProperty("App::PropertyLength", "cross_flat_width")
body.cross_flat_width = params["cross_flat_width"]
body.addProperty("App::PropertyLength", "hex_height")
body.hex_height = params["hex_height"]

# --- Helper Functions ---
def create_hex_sketch_on_plane(plane_name, z_offset):
    """Creates a hexagonal sketch on the specified plane with a Z offset."""
    sketch = body.newObject("Sketcher::SketchObject", f"HexSketch_{plane_name}")
    sketch.Plane = plane_name
    sketch.Locked = False
    
    # Calculate Hexagon Geometry
    # Cross flat width = 2 * apothem
    apothem = params["cross_flat_width"] / 2.0
    R_hex = apothem / math.cos(math.radians(30))
    tan30 = math.tan(math.radians(30))
    
    # Define vertices for a flat-sided hexagon (flats parallel to Y axis)
    # Center is at (0,0) in the sketch plane.
    # Plane YZ: X is horizontal, Y is vertical, Z is depth (normal).
    # We want the hexagon in the X-Y plane of the sketch.
    # Vertices:
    # 1. (A, -0.5*R)
    # 2. (R, 0)
    # 3. (A, 0.5*R)
    # 4. (-A, 0.5*R)
    # 5. (-R, 0)
    # 6. (-A, -0.5*R)
    
    p1 = App.Vector(apothem, -0.5 * R_hex, 0)
    p2 = App.Vector(R_hex, 0, 0)
    p3 = App.Vector(apothem, 0.5 * R_hex, 0)
    p4 = App.Vector(-apothem, 0.5 * R_hex, 0)
    p5 = App.Vector(-R_hex, 0, 0)
    p6 = App.Vector(-apothem, -0.5 * R_hex, 0)
    
    # Add Segments
    sketch.addGeometry(Part.LineSegment(p1, p2), False)
    sketch.addGeometry(Part.LineSegment(p2, p3), False)
    sketch.addGeometry(Part.LineSegment(p3, p4), False)
    sketch.addGeometry(Part.LineSegment(p4, p5), False)
    sketch.addGeometry(Part.LineSegment(p5, p6), False)
    sketch.addGeometry(Part.LineSegment(p6, p1), False)
    
    # Add Constraints to fix the shape
    # Constrain points to axes and distances
    # p2: (R, 0) -> On X axis (Local Y=0)
    sketch.addConstraint(Sketcher.Constraint("PointOnObject", 1, 2, 1, 1)) # Line 1 (p1-p2) point 2 on Line 1? No.
    # Let's use explicit coordinate constraints for robustness
    sketch.addConstraint(Sketcher.Constraint("XY", 1, 2, 0, R_hex, 0))
    sketch.addConstraint(Sketcher.Constraint("XY", 1, 3, 0, apothem, apothem*tan30))
    sketch.addConstraint(Sketcher.Constraint("XY", 1, 4, 0, -apothem, apothem*tan30))
    sketch.addConstraint(Sketcher.Constraint("XY", 1, 5, 0, -R_hex, 0))
    sketch.addConstraint(Sketcher.Constraint("XY", 1, 6, 0, -apothem, -apothem*tan30))
    sketch.addConstraint(Sketcher.Constraint("XY", 0, 1, 0, apothem, -apothem*tan30))
    
    # Close the loop constraint
    sketch.addConstraint(Sketcher.Constraint("Loop", 0, 1, 1, 6))
    
    # Move the sketch to the correct Z position
    # The sketch is on YZ plane. We need to move it along Z axis.
    # We use a Placement.
    sketch.Placement = App.Placement(App.Vector(0, 0, z_offset))
    
    return sketch

# --- Feature Construction ---

# 1. Handle Sketch (Cylinder)
# Attached to XY plane, centered at origin
handle_sketch = body.newObject("Sketcher::SketchObject", "HandleSketch")
handle_sketch.Plane = "XY_Plane"
handle_sketch.Locked = False

# Add Geometry
# Line for diameter
l1 = Part.LineSegment(App.Vector(0, 0, 0), App.Vector(params["handle_diameter"], 0, 0))
handle_sketch.addGeometry(l1, False)

# Circle for the handle end
c1 = Part.Circle(App.Vector(params["handle_diameter"]/2, 0, 0), App.Vector(0, 0, 1), params["handle_diameter"]/2)
handle_sketch.addGeometry(c1, False)

# Add Constraints
# Horizontal line on X axis
handle_sketch.addConstraint(Sketcher.Constraint("Horizontal", 0))
# Line starts at origin (Coincident with origin point implied by Plane)
# We need to constrain the end of the circle to be on the line.
# Actually, simpler: Line segment from 0 to D. Circle center at D/2, Radius D/2.
# Constraint: Circle center coincident with Midpoint of Line? Or just define line and circle independently.
# Let's use explicit coordinates or standard constraints.
# Line: Point A (0,0) to Point B (D,0).
# Circle: Center C (D/2, 0), Radius R = D/2.
# Constraint: Circle center coincident with Midpoint of Line? No, let's just constrain the circle center to the line.
handle_sketch.addConstraint(Sketcher.Constraint("Coincident", 1, 2, 0, 0)) # Circle center (1,2) on Line (0,0)
# Tangency between Circle and Line ends
handle_sketch.addConstraint(Sketcher.Constraint("PointOnObject", 1, 2, 0)) # Circle center on Line
# Distance from Circle Center to Line End is Radius
handle_sketch.addConstraint(Sketcher.Constraint("DistanceXY", 1, 2, 0, 1, 0, params["handle_diameter"]/2))

# 2. Handle Pad
handle_pad = body.newObject("PartDesign::Pad", "HandlePad")
handle_pad.Profile = handle_sketch
handle_pad.Length = params["handle_length"]
handle_pad.Midplane = False
handle_pad.setExpression("Length", "handle_length")
handle_pad.setExpression("Profile", "HandleSketch")

# 3. Hex End 1 (Positive Z)
# Create sketch on YZ plane, moved to Z = +hex_height/2
hex_sketch_1 = create_hex_sketch_on_plane("YZ_Plane", params["hex_height"]/2)

# Pad the hex end
hex_pad_1 = body.newObject("PartDesign::Pad", "HexPad1")
hex_pad_1.Profile = hex_sketch_1
hex_pad_1.Length = params["hex_height"]
hex_pad_1.Midplane = False
hex_pad_1.setExpression("Length", "hex_height")
hex_pad_1.setExpression("Profile", "HexSketch_YZ_Plane")

# 4. Hex End 2 (Negative Z)
# Create sketch on YZ plane, moved to Z = -hex_height/2
hex_sketch_2 = create_hex_sketch_on_plane("YZ_Plane", -params["hex_height"]/2)

# Pad the hex end
hex_pad_2 = body.newObject("PartDesign::Pad", "HexPad2")
hex_pad_2.Profile = hex_sketch_2
hex_pad_2.Length = params["hex_height"]
hex_pad_2.Midplane = False
hex_pad_2.setExpression("Length", "hex_height")
hex_pad_2.setExpression("Profile", "HexSketch_YZ_Plane")

# --- Finalize ---
doc.recompute()

# Save the file next to the script
script_path = Path(__file__).resolve()
output_path = script_path.with_name(script_path.stem + ".FCStd")
doc.saveAs(str(output_path))
