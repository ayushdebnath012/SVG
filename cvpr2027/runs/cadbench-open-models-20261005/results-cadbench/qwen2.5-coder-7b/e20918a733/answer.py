import FreeCAD
import Part
import PartDesign
import math

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create the gear body
gear_body = body.newObject("PartDesign::Pad", "GearBody")
gear_body.Profile = doc.addObject("Part::Circle", "GearProfile")
gear_body.Profile.Radius = 35  # pitch_diameter / 2
gear_body.Length = 2.25  # whole_depth

# Create the hub
hub = body.newObject("PartDesign::Pocket", "Hub")
hub.Profile = doc.addObject("Part::Circle", "HubProfile")
hub.Profile.Radius = 9  # hub_diameter / 2
hub.Length = 8  # hub_width

# Create the bore
bore = body.newObject("PartDesign::Pocket", "Bore")
bore.Profile = doc.addObject("Part::Circle", "BoreProfile")
bore.Profile.Radius = 4  # shaft_diameter / 2
bore.Length = 14  # overall_width

# Position the hub and bore
hub.Placement.Base = FreeCAD.Vector(0, 0, 2.25)  # Position hub at the top of the gear body
bore.Placement.Base = FreeCAD.Vector(0, 0, 2.25 - 8)  # Position bore at the bottom of the gear body

# Save the document
doc.saveAs("/app/answer.FCStd")
