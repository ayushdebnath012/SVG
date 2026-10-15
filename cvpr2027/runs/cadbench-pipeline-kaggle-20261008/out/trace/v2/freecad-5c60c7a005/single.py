import FreeCAD as App
import Part
from pathlib import Path
import os

# Ensure we are using FreeCAD 1.1 API patterns
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

# Create the base sketch on the XY plane
sketch = body.newObject("Sketcher::SketchObject", "BaseSketch")
sketch.Placement = App.Placement(App.Vector(0, 0, 0))
sketch.AttachmentSupport = (doc.getObject("XY_Plane"), [])
sketch.MapMode = "FlatFace"
sketch.ConstrainAuto = True
sketch.ConstrainFully = True

# Add a circle to the sketch representing the profile
# We will use expressions to drive the radius from the parameters
# Radius = Diameter / 2
# We start with Section 1 as the base profile, but since we need a stepped shaft,
# we will actually build this using a single Pad with a complex profile or multiple Pads.
# Given the requirement for "smooth stepped shaft" and "coaxial cylindrical sections",
# the most robust parametric way in PartDesign without complex boolean sketches is to
# create a single Pad with a profile that is a series of connected lines and arcs,
# OR create multiple Pads stacked on top of each other.
# The prompt asks for "eight coaxial cylindrical sections... stacked sequentially".
# This implies a stack of Pads is the most logical interpretation of "stacked sequentially end-to-end".
# However, to ensure a "smooth" transition (fillets) and a single solid, we will create
# the profile for the first section, pad it, then add subsequent sections as Pads.
# Actually, a single Pad with a complex profile (lines/arcs) is often cleaner for a single solid,
# but "stacked sequentially" strongly suggests a sequence of features.
# Let's implement the "Stacked Pads" approach as it maps 1:1 to the section definitions.
# To make it one solid, we just need to ensure they are stacked.

# We need to create 8 sketches, one for each section's profile, or one sketch and 8 Pads?
# If we use one sketch, we define the full outline.
# If we use 8 sketches, we define each step.
# Let's use the "Single Sketch + Complex Profile" approach for a truly single feature tree logic,
# BUT the prompt says "built from sketches and PartDesign features... driven by named document objects".
# And "stacked sequentially".
# Let's go with the most explicit interpretation: 8 Pads, each corresponding to a section.
# To do this efficiently, we will create one sketch that defines the profile of Section 1.
# Then we will create 7 more sketches (or reuse the first one with different constraints/expressions)
# for the subsequent sections.
# Actually, the cleanest way to get 8 distinct sections driven by 8 pairs of parameters is:
# Create 8 Sketches. Sketch 1 defines the profile for Section 1. Sketch 2 defines Section 2, etc.
# But wait, if we just pad them, we get a stack.
# Let's refine: We will create ONE sketch that contains the profile for the FIRST section.
# Then we will create 7 more sketches, each containing a circle for the subsequent sections.
# This ensures every parameter is directly linked to a feature.

# --- Section 1 ---
sketch1 = body.newObject("Sketcher::SketchObject", "Sketch_Section1")
sketch1.Placement = App.Placement(App.Vector(0, 0, 0))
sketch1.AttachmentSupport = (doc.getObject("XY_Plane"), [])
sketch1.MapMode = "FlatFace"
# Add circle for Section 1
circle1 = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.section_1_diameter / 2.0)
sketch1.addGeometry(circle1, False)
# Add center point constraint
sketch1.addConstraint(Sketcher.Constraint("Center", 0, 0))
sketch1.addConstraint(Sketcher.Constraint("Radius", 0, 0, params.section_1_diameter / 2.0))

# Pad Section 1
pad1 = body.newObject("PartDesign::Pad", "Pad_Section1")
pad1.Profile = sketch1
pad1.Length = params.section_1_length
pad1.Type = "Solid"
pad1.Midplane = False
pad1.Reversed = False

# --- Section 2 ---
sketch2 = body.newObject("Sketcher::SketchObject", "Sketch_Section2")
sketch2.Placement = App.Placement(App.Vector(0, 0, params.section_1_length)) # Offset to start where Pad1 ended
sketch2.AttachmentSupport = (doc.getObject("XY_Plane"), [])
sketch2.MapMode = "FlatFace"
circle2 = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.section_2_diameter / 2.0)
sketch2.addGeometry(circle2, False)
sketch2.addConstraint(Sketcher.Constraint("Center", 0, 0))
sketch2.addConstraint(Sketcher.Constraint("Radius", 0, 0, params.section_2_diameter / 2.0))

pad2 = body.newObject("PartDesign::Pad", "Pad_Section2")
pad2.Profile = sketch2
pad2.Length = params.section_2_length
pad2.Type = "Solid"
pad2.Midplane = False
pad2.Reversed = False

# --- Section 3 ---
sketch3 = body.newObject("Sketcher::SketchObject", "Sketch_Section3")
sketch3.Placement = App.Placement(App.Vector(0, 0, params.section_1_length + params.section_2_length))
sketch3.AttachmentSupport = (doc.getObject("XY_Plane"), [])
sketch3.MapMode = "FlatFace"
circle3 = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.section_3_diameter / 2.0)
sketch3.addGeometry(circle3, False)
sketch3.addConstraint(Sketcher.Constraint("Center", 0, 0))
sketch3.addConstraint(Sketcher.Constraint("Radius", 0, 0, params.section_3_diameter / 2.0))

pad3 = body.newObject("PartDesign::Pad", "Pad_Section3")
pad3.Profile = sketch3
pad3.Length = params.section_3_length
pad3.Type = "Solid"
pad3.Midplane = False
pad3.Reversed = False

# --- Section 4 ---
sketch4 = body.newObject("Sketcher::SketchObject", "Sketch_Section4")
sketch4.Placement = App.Placement(App.Vector(0, 0, params.section_1_length + params.section_2_length + params.section_3_length))
sketch4.AttachmentSupport = (doc.getObject("XY_Plane"), [])
sketch4.MapMode = "FlatFace"
circle4 = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.section_4_diameter / 2.0)
sketch4.addGeometry(circle4, False)
sketch4.addConstraint(Sketcher.Constraint("Center", 0, 0))
sketch4.addConstraint(Sketcher.Constraint("Radius", 0, 0, params.section_4_diameter / 2.0))

pad4 = body.newObject("PartDesign::Pad", "Pad_Section4")
pad4.Profile = sketch4
pad4.Length = params.section_4_length
pad4.Type = "Solid"
pad4.Midplane = False
pad4.Reversed = False

# --- Section 5 ---
sketch5 = body.newObject("Sketcher::SketchObject", "Sketch_Section5")
sketch5.Placement = App.Placement(App.Vector(0, 0, params.section_1_length + params.section_2_length + params.section_3_length + params.section_4_length))
sketch5.AttachmentSupport = (doc.getObject("XY_Plane"), [])
sketch5.MapMode = "FlatFace"
circle5 = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.section_5_diameter / 2.0)
sketch5.addGeometry(circle5, False)
sketch5.addConstraint(Sketcher.Constraint("Center", 0, 0))
sketch5.addConstraint(Sketcher.Constraint("Radius", 0, 0, params.section_5_diameter / 2.0))

pad5 = body.newObject("PartDesign::Pad", "Pad_Section5")
pad5.Profile = sketch5
pad5.Length = params.section_5_length
pad5.Type = "Solid"
pad5.Midplane = False
pad5.Reversed = False

# --- Section 6 ---
sketch6 = body.newObject("Sketcher::SketchObject", "Sketch_Section6")
sketch6.Placement = App.Placement(App.Vector(0, 0, params.section_1_length + params.section_2_length + params.section_3_length + params.section_4_length + params.section_5_length))
sketch6.AttachmentSupport = (doc.getObject("XY_Plane"), [])
sketch6.MapMode = "FlatFace"
circle6 = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.section_6_diameter / 2.0)
sketch6.addGeometry(circle6, False)
sketch6.addConstraint(Sketcher.Constraint("Center", 0, 0))
sketch6.addConstraint(Sketcher.Constraint("Radius", 0, 0, params.section_6_diameter / 2.0))

pad6 = body.newObject("PartDesign::Pad", "Pad_Section6")
pad6.Profile = sketch6
pad6.Length = params.section_6_length
pad6.Type = "Solid"
pad6.Midplane = False
pad6.Reversed = False

# --- Section 7 ---
sketch7 = body.newObject("Sketcher::SketchObject", "Sketch_Section7")
sketch7.Placement = App.Placement(App.Vector(0, 0, params.section_1_length + params.section_2_length + params.section_3_length + params.section_4_length + params.section_5_length + params.section_6_length))
sketch7.AttachmentSupport = (doc.getObject("XY_Plane"), [])
sketch7.MapMode = "FlatFace"
circle7 = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.section_7_diameter / 2.0)
sketch7.addGeometry(circle7, False)
sketch7.addConstraint(Sketcher.Constraint("Center", 0, 0))
sketch7.addConstraint(Sketcher.Constraint("Radius", 0, 0, params.section_7_diameter / 2.0))

pad7 = body.newObject("PartDesign::Pad", "Pad_Section7")
pad7.Profile = sketch7
pad7.Length = params.section_7_length
pad7.Type = "Solid"
pad7.Midplane = False
pad7.Reversed = False

# --- Section 8 ---
sketch8 = body.newObject("Sketcher::SketchObject", "Sketch_Section8")
sketch8.Placement = App.Placement(App.Vector(0, 0, params.section_1_length + params.section_2_length + params.section_3_length + params.section_4_length + params.section_5_length + params.section_6_length + params.section_7_length))
sketch8.AttachmentSupport = (doc.getObject("XY_Plane"), [])
sketch8.MapMode = "FlatFace"
circle8 = Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.section_8_diameter / 2.0)
sketch8.addGeometry(circle8, False)
sketch8.addConstraint(Sketcher.Constraint("Center", 0, 0))
sketch8.addConstraint(Sketcher.Constraint("Radius", 0, 0, params.section_8_diameter / 2.0))

pad8 = body.newObject("PartDesign::Pad", "Pad_Section8")
pad8.Profile = sketch8
pad8.Length = params.section_8_length
pad8.Type = "Solid"
pad8.Midplane = False
pad8.Reversed = False

# Add Fillets for smooth transitions between sections
# We need to find the edges between the pads.
# Since the pads are stacked, the top face of Pad_i and bottom face of Pad_{i+1} are coincident.
# The transition edge is the circular edge at the junction.
# We will add fillets between Pad_i and Pad_{i+1}.

# Helper to get the top edge of a pad (assuming Z is up)
# In PartDesign, the top face of a Pad is usually the last face created in the Z direction.
# We can access the top face of a pad and get its edge.
# However, getting the specific edge index dynamically can be tricky without a loop.
# Let's assume the standard orientation: Pad grows in +Z.
# The edge between Pad_i and Pad_{i+1} is the top edge of Pad_i.

# We will add fillets between each adjacent pair.
# Fillet Size: Let's use a small value, e.g., 1.0 mm, or derive from parameters?
# The prompt doesn't specify fillet size, just "smooth". A standard 1mm or 2mm is good.
# Let's use 2.0 mm for a noticeable smooth step.
fillet_size = 2.0

# Function to get the top edge of a Pad feature
def get_top_edge(pad_obj):
    # Get the top face of the pad
    # The pad creates a solid. The top face is the one with the highest Z.
    # We can iterate through the faces of the pad's shape.
    # However, in FreeCAD 1.1, we can often rely on the fact that the top face is the last one added 
    # if we are careful, or we can query the shape.
    # A more robust way in script: Get the shape, find the face with max Z, get its edge.
    shape = pad_obj.Shape
    if not shape:
        return None
    
    # Get all edges of the shape
    edges = shape.Edges()
    # We are looking for the circular edge at the top.
    # Since it's a cylinder, there are two circular edges (top and bottom) and maybe others if complex.
    # Here, each pad is a cylinder.
    # We need to distinguish top from bottom.
    # The top face normal should be +Z.
    faces = shape.Faces()
    top_face = None
    max_z = -1e9
    
    for face in faces
