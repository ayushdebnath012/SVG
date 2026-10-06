import FreeCAD
import Part
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create the gear body
gear_body = body.newObject("PartDesign::Pad", "GearBody")
gear_body.Length = 3.375  # whole_depth
gear_body.Profile = Part.makeCircle(39)  # outer_diameter / 2

# Create the hub
hub = body.newObject("PartDesign::Pocket", "Hub")
hub.Length = 10  # hub_width
hub.Profile = Part.makeCircle(22.5)  # hub_diameter / 2

# Create the bore
bore = body.newObject("PartDesign::Pocket", "Bore")
bore.Length = 10  # hub_width
bore.Profile = Part.makeCircle(5)  # shaft_diameter / 2

# Position the hub and bore
hub.Placement.Base = FreeCAD.Vector(0, 0, 1.6875)  # whole_depth / 2
bore.Placement.Base = FreeCAD.Vector(0, 0, 1.6875)  # whole_depth / 2

# Save the document
doc.saveAs("/app/answer.FCStd")
