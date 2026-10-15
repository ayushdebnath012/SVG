import FreeCAD as App
import Part
import Sketcher
from pathlib import Path

# Create a new document
doc = App.newDocument("FlangePart")

# 1. Create Parameter Object
params = doc.addObject("App::VarSet", "Parameters")
params.addProperty("App::PropertyLength", "outer_diameter", "Dimensions", "Outer flange diameter")
params.addProperty("App::PropertyLength", "flange_thickness", "Dimensions", "Flange thickness")
params.addProperty("App::PropertyLength", "bore_diameter", "Dimensions", "Central bore diameter")
params.addProperty("App::PropertyLength", "bolt_circle_diameter", "Dimensions", "Bolt circle diameter")
params.addProperty("App::PropertyLength", "bolt_hole_diameter", "Dimensions", "Bolt hole diameter")
params.addProperty("App::PropertyInteger", "number_bolt_holes", "Dimensions", "Number of bolt holes")

params.outer_diameter = 66.675
params.flange_thickness = 13.49375
params.bore_diameter = 23.8125
params.bolt_circle_diameter = 53.18125
params.bolt_hole_diameter = 6.746875
params.number_bolt_holes = 4

# 2. Create PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# 3. Create Base Sketch (Flange Outer Shape) on XY Plane
base_sketch = body.newObject("Sketcher::SketchObject", "FlangeProfile")
base_sketch.Placement = App.Placement() # Default is (0,0,0) with identity rotation
base_sketch.Constraints = []
base_sketch.Locked = True
# Create a circle for the flange outer edge
base_sketch.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.outer_diameter / 2.0))
# Add constraints to define the circle properly
base_sketch.Constraints.append(Sketcher.Constraint("Axis", 0, 1)) 
base_sketch.Constraints.append(Sketcher.Constraint("Size2D", 0, 1, 0, params.outer_diameter))

# 4. Create Pad Feature to form the solid block
pad = body.newObject("PartDesign::Pad", "Pad")
pad.Profile = base_sketch
pad.Length = params.flange_thickness
pad.Type = "Solid"
pad.Reversed = False
pad.Force2D = False

# 5. Create Central Bore Sketch on the top face of the pad
# We attach this sketch to the top face of the Pad. 
# In PartDesign, we can use the face of the Pad as a support.
# We will use the Pad as the reference plane/face.
bore_sketch = body.newObject("Sketcher::SketchObject", "BoreSketch")
# To place on the top face, we usually need an offset or a specific face selection.
# Since we can't easily select by index in headless, let's create the sketch on a plane parallel to XY 
# at height = flange_thickness. This effectively creates a "virtual" top face.
bore_sketch.Placement = App.Placement(App.Vector(0, 0, params.flange_thickness))
# Attach to XY plane but lifted
bore_sketch.AttachmentSupport = (doc.getObject("XY_Plane"), ["1"]) 

# Add circle for the bore
bore_sketch.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.bore_diameter / 2.0))
bore_sketch.Constraints.append(Sketcher.Constraint("Axis", 0, 1))
bore_sketch.Constraints.append(Sketcher.Constraint("Size2D", 0, 1, 0, params.bore_diameter))

# 6. Create Pocket Feature for the Bore
pocket = body.newObject("PartDesign::Pocket", "CentralBore")
pocket.Profile = bore_sketch
pocket.Type = "ThroughAll" # This ensures it goes through the entire body regardless of thickness

# 7. Create Bolt Hole Pattern Sketch
# We need a sketch on the top face again, offset by bolt circle diameter.
bolt_sketch = body.newObject("Sketcher::SketchObject", "BoltPatternSketch")
bolt_sketch.Placement = App.Placement(App.Vector(0, 0, params.flange_thickness))
bolt_sketch.AttachmentSupport = (doc.getObject("XY_Plane"), ["1"])

# Add a circle for the bolt hole
bolt_sketch.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.bolt_hole_diameter / 2.0))
bolt_sketch.Constraints.append(Sketcher.Constraint("Axis", 0, 1))
bolt_sketch.Constraints.append(Sketcher.Constraint("Size2D", 0, 1, 0, params.bolt_hole_diameter))

# 8. Create Polar Pattern Feature
# The pattern needs to be defined on the sketch itself or as a separate feature.
# In PartDesign::PolarPattern, we usually select the feature (the sketch) and define axis and angle.
pattern = body.newObject("PartDesign::PolarPattern", "BoltPattern")
pattern.Originals = [bolt_sketch]
# Axis is Z axis
pattern.Axis = (doc.getObject("Z_Axis"), [""])
pattern.Angle = 360.0
pattern.Occurrences = params.number_bolt_holes
pattern.Distribute = True # Distribute evenly
pattern.Placement = App.Placement() # Base placement

# 9. Save the document
# Derive path from __file__
output_path = Path(__file__).with_suffix(".FCStd")
doc.saveAs(str(output_path))

# Recompute to ensure all features are calculated before saving
doc.recompute()
