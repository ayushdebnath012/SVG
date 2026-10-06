import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Define the key parameters
outside_diameter = 8.0
inner_diameter = 4.2
overall_height = 0.6
thickness = 0.4
cone_height = 0.2

# Create a circular ring
ring = body.newObject("PartDesign::Pad", "Ring")
ring.Profile = doc.addObject("Part::Circle", "Circle")
ring.Profile.Radius = (outside_diameter - inner_diameter) / 2
ring.Length = overall_height
ring.LengthFillet = 0

# Create a conical section
cone = body.newObject("PartDesign::Pocket", "Cone")
cone.Profile = doc.addObject("Part::Circle", "ConeCircle")
cone.Profile.Radius = (outside_diameter - inner_diameter) / 2
cone.Length = cone_height
cone.LengthFillet = 0

# Create a cutout for the conical section
cutout = body.newObject("PartDesign::Cut", "Cutout")
cutout.Base = ring
cutout.Tool = cone

# Set the document properties
doc.setUnits("mm", "mm", "mm")
doc.recompute()

# Save the document
doc.saveAs("/app/answer.FCStd")
