import FreeCAD as App
import Part
from pathlib import Path

# Create a new document
doc = App.newDocument("SteppedShaft")

# Create the main Body
body = doc.addObject("PartDesign::Body", "Body")
body.Placement = App.Placement(App.Vector(0, 0, 0))

# Create a VarSet to hold all parameters for easy editing
params = body.newObject("App::VarSet", "Parameters")

# Define the 8 sections with their specific diameters and lengths
# Section 1
params.addProperty("App::PropertyLength", "section_1_diameter", "Dimensions", "Section 1 Diameter")
params.section_1_diameter = 10.0
params.addProperty("App::PropertyLength", "section_1_length", "Dimensions", "Section 1 Length")
params.section_1_length = 20.0

# Section 2
params.addProperty("App::PropertyLength", "section_2_diameter", "Dimensions", "Section 2 Diameter")
params.section_2_diameter = 15.0
params.addProperty("App::PropertyLength", "section_2_length", "Dimensions", "Section 2 Length")
params.section_2_length = 30.0

# Section 3
params.addProperty("App::PropertyLength", "section_3_diameter", "Dimensions", "Section 3 Diameter")
params.section_3_diameter = 20.0
params.addProperty("App::PropertyLength", "section_3_length", "Dimensions", "Section 3 Length")
params.section_3_length = 40.0

# Section 4
params.addProperty("App::PropertyLength", "section_4_diameter", "Dimensions", "Section 4 Diameter")
params.section_4_diameter = 40.0
params.addProperty("App::PropertyLength", "section_4_length", "Dimensions", "Section 4 Length")
params.section_4_length = 10.0

# Section 5
params.addProperty("App::PropertyLength", "section_5_diameter", "Dimensions", "Section 5 Diameter")
params.section_5_diameter = 30.0
params.addProperty("App::PropertyLength", "section_5_length", "Dimensions", "Section 5 Length")
params.section_5_length = 20.0

# Section 6
params.addProperty("App::PropertyLength", "section_6_diameter", "Dimensions", "Section 6 Diameter")
params.section_6_diameter = 25.0
params.addProperty("App::PropertyLength", "section_6_length", "Dimensions", "Section 6 Length")
params.section_6_length = 25.0

# Section 7
params.addProperty("App::PropertyLength", "section_7_diameter", "Dimensions", "Section 7 Diameter")
params.section_7_diameter = 20.0
params.addProperty("App::PropertyLength", "section_7_length", "Dimensions", "Section 7 Length")
params.section_7_length = 20.0

# Section 8
params.addProperty("App::PropertyLength", "section_8_diameter", "Dimensions", "Section 8 Diameter")
params.section_8_diameter = 50.0
params.addProperty("App::PropertyLength", "section_8_length", "Dimensions", "Section 8 Length")
params.section_8_length = 20.0

# Helper function to create a sketch and pad for a section
def create_section(section_idx, body, params, current_z):
    # Create Sketch
    sketch_name = f"Sketch_Section{section_idx}"
    sketch = body.newObject("Sketcher::SketchObject", sketch_name)
    sketch.Placement = App.Placement(App.Vector(0, 0, current_z))
    sketch.AttachmentSupport = (doc.getObject("XY_Plane"), [])
    sketch.MapMode = "FlatFace"
    
    # Add circle to the sketch
    diameter = getattr(params, f"section_{section_idx}_diameter")
    radius = diameter / 2.0
    circle = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), radius)
    sketch.addGeometry(circle, False)
    
    # Add constraints
    sketch.addConstraint(Sketcher.Constraint("Center", 0, 0))
    sketch.addConstraint(Sketcher.Constraint("Radius", 0, 0, radius))
    
    # Create Pad
    pad_name = f"Pad_Section{section_idx}"
    pad = body.newObject("PartDesign::Pad", pad_name)
    pad.Profile = sketch
    pad.Length = getattr(params, f"section_{section_idx}_length")
    pad.Type = "Solid"
    pad.Midplane = False
    pad.Reversed = False
    
    return pad

# Create the 8 sections sequentially
current_z = 0.0
pads = []
for i in range(1, 9):
    pad = create_section(i, body, params, current_z)
    pads.append(pad)
    current_z += getattr(params, f"section_{i}_length")

# Add Fillets for smooth transitions between sections
# We will add fillets between each adjacent pair of pads.
# The edge to fillet is the top edge of the lower pad (which is also the bottom edge of the upper pad).
# Since the pads are stacked, the top face of Pad_i and bottom face of Pad_{i+1} are coincident.
# The edge is the circular perimeter at that junction.

# We need to find the edge. In a simple stack of cylinders, the top edge of a Pad is the one with the highest Z.
# We can iterate through the edges of the pad's shape to find the top one.
fillet_size = 2.0

for i in range(len(pads) - 1):
    lower_pad = pads[i]
    upper_pad = pads[i+1]
    
    # Get the shape of the lower pad
    shape = lower_pad.Shape
    if not shape:
        continue
        
    # Find the top edge (highest Z)
    top_edge = None
    max_z = -1e9
    
    for edge in shape.Edges():
        # Get the bounding box of the edge to estimate Z
        bbox = edge.BoundingBox
        z_center = (bbox.ZMin + bbox.ZMax) / 2.0
        if z_center > max_z:
            max_z = z_center
            top_edge = edge
            
    if top_edge:
        # Add fillet
        chamfer = body.newObject("PartDesign::Chamfer", f"Chamfer_{i+1}")
        chamfer.Base = (lower_pad, [top_edge])
        chamfer.Size = fillet_size
        chamfer.Type = "Radius"
        chamfer.Radius = fillet_size

# Recompute the document
doc.recompute()

# Determine output path based on __file__
script_path = Path(__file__).resolve()
output_path = script_path.with_name(script_path.stem + ".FCStd")

# Save the document
doc.saveAs(str(output_path))
