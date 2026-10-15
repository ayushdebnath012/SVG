import FreeCAD as App
import Part
import Sketcher
from pathlib import Path
import os

# Define parameters as named document objects for editability
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
base_sketch.Placement = App.Placement(App.Vector(0, 0, 0))
base_sketch.Constraints = []
base_sketch.Locked = True
# Create a circle for the flange outer edge
base_sketch.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), params.outer_diameter / 2.0))
base_sketch.Constraints.append(Sketcher.Constraint("Axis", 0, 1)) # Ensure circle axis aligns with Z
base_sketch.Constraints.append(Sketcher.Constraint("Size2D", 0, 1, 0, params.outer_diameter))

# 4. Create Pad Feature to form the solid block
pad = body.newObject("PartDesign::Pad", "Pad")
pad.Profile = base_sketch
pad.Length = params.flange_thickness
pad.Type = "Solid"
pad.Reversed = False
pad.Force2D = False

# 5. Create Central Bore Sketch on the top face of the pad
# We need to reference the top face of the pad. In PartDesign, we can use the Body's faces.
# However, a more robust way for scripts without GUI interaction is to create a new sketch on a plane offset 
# or simply reference the face created by the pad.
# Since we are in headless, let's create a sketch on the top face of the Pad.
# We get the face ID from the Pad's resulting solid. But to keep it purely feature-tree driven without 
# querying the solid immediately, we can assume the Pad creates a face on the top.
# Actually, the standard way in PartDesign for a through hole on a specific feature is to put the sketch 
# on that feature's face.
# Let's create a specific sketch for the bore.

bore_sketch = body.newObject("Sketcher::SketchObject", "BoreSketch")
# We need to attach this to the top face of the Pad. 
# In PartDesign, we can use the face of the Pad as a support.
# Get the last feature (Pad) and its resulting face. 
# Alternatively, we can use a Plane offset from the base if we didn't have a solid yet, but we do.
# Let's attach to the Pad's top face.
# Note: In FreeCAD 1.1, accessing face IDs directly from a script without GUI can be tricky.
# A reliable method for a through hole is to use the Pad as the reference plane/face.
# We will use the Pad as the support for the sketch.
bore_sketch.Placement = App.Placement(App.Vector(0, 0, 0)) 
# To place on the top face, we usually need an offset or a specific face selection.
# Since we can't easily select by index in headless, let's create the sketch on a plane parallel to XY 
# at height = flange_thickness. This effectively creates a "virtual" top face.
bore_sketch.Placement = App.Placement(App.Vector(0, 0, params.flange_thickness))
bore_sketch.AttachmentSupport = (doc.getObject("XY_Plane"), ["1"]) # Lifted Z

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
pattern.Placement = App.Placement(App.Vector(0, 0, 0)) # Base placement

# 9. Apply Fillets/Chamfers if needed (Optional based on description, but good practice)
# The description doesn't explicitly ask for fillets, but a flange usually has one.
# Let's skip specific fillets unless implied, sticking strictly to "mounting flange... bore... bolt holes".
# No chamfer/fillet requested in the specific parameter list, so we stop here.

# 10. Save the document
# Derive path from __file__
output_path = Path(__file__).with_suffix(".FCStd")
doc.saveAs(str(output_path))

# Recompute to ensure all features are calculated before saving
doc.recompute()

# Clean up temporary variables
del params
del body
del base_sketch
del pad
del bore_sketch
del pocket
del bolt_sketch
del pattern
del doc
