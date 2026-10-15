import FreeCAD as App
import Part
from pathlib import Path

# Create a new document
doc = App.newDocument("SteppedShaft")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")
doc.recompute()

# --- Parameters ---
# We will store parameters in a VarSet object attached to the Body
params = body.newObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "shaft_section_1_diameter", "Dimensions", "Diameter of section 1")
params.addProperty("App::PropertyLength", "shaft_section_1_length", "Dimensions", "Length of section 1")
params.addProperty("App::PropertyLength", "shaft_section_2_diameter", "Dimensions", "Diameter of section 2")
params.addProperty("App::PropertyLength", "shaft_section_2_length", "Dimensions", "Length of section 2")
params.addProperty("App::PropertyLength", "shaft_section_3_diameter", "Dimensions", "Diameter of section 3")
params.addProperty("App::PropertyLength", "shaft_section_3_length", "Dimensions", "Length of section 3")
params.addProperty("App::PropertyLength", "shaft_section_4_diameter", "Dimensions", "Diameter of section 4")
params.addProperty("App::PropertyLength", "shaft_section_4_length", "Dimensions", "Length of section 4")
params.addProperty("App::PropertyLength", "shaft_section_5_diameter", "Dimensions", "Diameter of section 5")
params.addProperty("App::PropertyLength", "shaft_section_5_length", "Dimensions", "Length of section 5")

# Set default values as per description
params.shaft_section_1_diameter = 10.0
params.shaft_section_1_length = 40.0
params.shaft_section_2_diameter = 15.0
params.shaft_section_2_length = 30.0
params.shaft_section_3_diameter = 20.0
params.shaft_section_3_length = 40.0
params.shaft_section_4_diameter = 40.0
params.shaft_section_4_length = 10.0
params.shaft_section_5_diameter = 30.0
params.shaft_section_5_length = 20.0

# --- Helper to create a parametric rectangle sketch ---
def create_parametric_rectangle_sketch(body, name, d, l, z_offset=0):
    """
    Creates a sketch with a rectangle of diameter d and length l, centered at (0,0,z_offset).
    Returns the sketch object.
    """
    sketch = body.newObject("Sketcher::SketchObject", name)
    # Attach to XY plane
    sketch.Placement = App.Placement(App.Vector(0, 0, z_offset))
    sketch.Support = (doc.getObject("XY_Plane"), [])
    sketch.MapMode = "FlatFace"
    
    # Add 4 lines forming a rectangle
    # We add them with initial geometry, then constrain them.
    # To make them parametric, we will use constraints with expressions.
    
    # Line 1: Bottom (-d/2, -l/2) to (d/2, -l/2)
    p1 = App.Vector(-d/2, -l/2, 0)
    p2 = App.Vector(d/2, -l/2, 0)
    sketch.addGeometry(Part.LineSegment(p1, p2), False)
    
    # Line 2: Right (d/2, -l/2) to (d/2, l/2)
    p3 = App.Vector(d/2, -l/2, 0)
    p4 = App.Vector(d/2, l/2, 0)
    sketch.addGeometry(Part.LineSegment(p3, p4), False)
    
    # Line 3: Top (d/2, l/2) to (-d/2, l/2)
    p5 = App.Vector(d/2, l/2, 0)
    p6 = App.Vector(-d/2, l/2, 0)
    sketch.addGeometry(Part.LineSegment(p5, p6), False)
    
    # Line 4: Left (-d/2, l/2) to (-d/2, -l/2)
    p7 = App.Vector(-d/2, l/2, 0)
    p8 = App.Vector(-d/2, -l/2, 0)
    sketch.addGeometry(Part.LineSegment(p7, p8), False)
    
    # Constraints
    # 1. Coincident corners
    sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 2, 1, 1)) # p2-p3
    sketch.addConstraint(Sketcher.Constraint("Coincident", 1, 2, 2, 1)) # p4-p5
    sketch.addConstraint(Sketcher.Constraint("Coincident", 2, 2, 3, 1)) # p6-p7
    sketch.addConstraint(Sketcher.Constraint("Coincident", 3, 2, 0, 1)) # p8-p1
    
    # 2. Horizontal/Vertical
    sketch.addConstraint(Sketcher.Constraint("Horizontal", 0, 1))
    sketch.addConstraint(Sketcher.Constraint("Horizontal", 2, 1))
    sketch.addConstraint(Sketcher.Constraint("Vertical", 1, 1))
    sketch.addConstraint(Sketcher.Constraint("Vertical", 3, 1))
    
    # 3. Equal lengths (opposite sides)
    sketch.addConstraint(Sketcher.Constraint("Equal", 0, 1, 2, 1))
    sketch.addConstraint(Sketcher.Constraint("Equal", 1, 1, 3, 1))
    
    # 4. Centering (Midpoint at origin)
    # Using "Center" constraint on the lines relative to the plane
    sketch.addConstraint(Sketcher.Constraint("Center", 0, 1))
    sketch.addConstraint(Sketcher.Constraint("Center", 1, 1))
    
    # 5. Drive dimensions with expressions
    # We need to set the length of the horizontal lines to 'd' and vertical to 'l'.
    # We can use "Distance" constraint between endpoints? No, simpler to use "Equal" with a point?
    # Actually, we can use "Distance" constraint between two points on the line?
    # Or we can use "Equal" constraint between the line length and a parameter.
    # Sketcher supports "Equal" between a line length and a parameter expression.
    # Syntax: Sketcher.Constraint("Equal", line_index, 1, param_name) ? 
    # No, standard way is to use "Distance" between two points, or "Equal" between two lines.
    # To drive a line length from a parameter, we can use:
    # Sketcher.Constraint("Distance", line_index, 1, "Expression") -> This sets the length of the line.
    # Let's try setting the length of Line 0 (horizontal) to 'd'.
    # And Line 1 (vertical) to 'l'.
    
    # Note: The indices in constraints refer to the geometry index in the sketch.
    # Line 0 is horizontal. Line 1 is vertical.
    
    # Set length of Line 0 to d
    sketch.addConstraint(Sketcher.Constraint("Distance", 0, 1, "Parameters.shaft_section_1_diameter"))
    # Set length of Line 1 to l
    sketch.addConstraint(Sketcher.Constraint("Distance", 1, 1, "Parameters.shaft_section_1_length"))
    
    return sketch

# --- Create Sketches for each section ---
# Section 1
sk1 = create_parametric_rectangle_sketch(body, "Sketch_Section1", 
                                          params.shaft_section_1_diameter, 
                                          params.shaft_section_1_length, 0)

# Section 2 (Offset by L1)
sk2 = create_parametric_rectangle_sketch(body, "Sketch_Section2", 
                                          params.shaft_section_2_diameter, 
                                          params.shaft_section_2_length, 
                                          params.shaft_section_1_length)

# Section 3 (Offset by L1+L2)
sk3 = create_parametric_rectangle_sketch(body, "Sketch_Section3", 
                                          params.shaft_section_3_diameter, 
                                          params.shaft_section_3_length, 
                                          params.shaft_section_1_length + params.shaft_section_2_length)

# Section 4 (Offset by L1+L2+L3)
sk4 = create_parametric_rectangle_sketch(body, "Sketch_Section4", 
                                          params.shaft_section_4_diameter, 
                                          params.shaft_section_4_length, 
                                          params.shaft_section_1_length + params.shaft_section_2_length + params.shaft_section_3_length)

# Section 5 (Offset by L1+L2+L3+L4)
sk5 = create_parametric_rectangle_sketch(body, "Sketch_Section5", 
                                          params.shaft_section_5_diameter, 
                                          params.shaft_section_5_length, 
                                          params.shaft_section_1_length + params.shaft_section_2_length + params.shaft_section_3_length + params.shaft_section_4_length)

# --- Create Pads for each section ---
# Pad 1
pad1 = body.newObject("PartDesign::Pad", "Pad_Section1")
pad1.Profile = sk1
pad1.Length = params.shaft_section_1_length
pad1.Type = "Solid"

# Pad 2
pad2 = body.newObject("PartDesign::Pad", "Pad_Section2")
pad2.Profile = sk2
pad2.Length = params.shaft_section_2_length
pad2.Type = "Solid"

# Pad 3
pad3 = body.newObject("PartDesign::Pad", "Pad_Section3")
pad3.Profile = sk3
pad3.Length = params.shaft_section_3_length
pad3.Type = "Solid"

# Pad 4
pad4 = body.newObject("PartDesign::Pad", "Pad_Section4")
pad4.Profile = sk4
pad4.Length = params.shaft_section_4_length
pad4.Type = "Solid"

# Pad 5
pad5 = body.newObject("PartDesign::Pad", "Pad_Section5")
pad5.Profile = sk5
pad5.Length = params.shaft_section_5_length
pad5.Type = "Solid"

# --- Recompute and Save ---
doc.recompute()

# Save the file next to the script
script_path = Path(__file__).resolve()
output_path = script_path.with_name(script_path.stem + ".FCStd")
doc.saveAs(str(output_path))
