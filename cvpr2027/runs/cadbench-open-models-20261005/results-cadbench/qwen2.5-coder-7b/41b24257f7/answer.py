import FreeCAD
import Part
import PartDesign
import math

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create a cylindrical gear body
gear_body = body.newObject("PartDesign::Pad", "GearBody")
gear_body.Profile = doc.addObject("Part::Circle", "GearProfile")
gear_body.Profile.Radius = 24  # Half of the pitch diameter
gear_body.Length = 52  # Outer diameter

# Create a central bore
bore = body.newObject("PartDesign::Pocket", "Bore")
bore.Profile = doc.addObject("Part::Circle", "BoreProfile")
bore.Profile.Radius = 5  # Half of the shaft diameter
bore.Length = 52  # Outer diameter

# Create a hub
hub = body.newObject("PartDesign::Pad", "Hub")
hub.Profile = doc.addObject("Part::Circle", "HubProfile")
hub.Profile.Radius = 19  # Half of the hub diameter
hub.Length = 30  # Overall width

# Position the hub concentrically with the gear body
hub.Placement.Base = FreeCAD.Vector(0, 0, 26)  # Center of the gear body

# Save the document
doc.saveAs("/app/answer.FCStd")
