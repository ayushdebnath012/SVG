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
gear_body.Profile.Radius = 60  # Half of the pitch diameter
gear_body.Length = 123  # Outer diameter
gear_body.LengthFilletRadius = 0

# Create a hub
hub = body.newObject("PartDesign::Pocket", "Hub")
hub.Profile = doc.addObject("Part::Circle", "HubProfile")
hub.Profile.Radius = 27.5  # Half of the hub diameter
hub.Length = 10  # Hub width
hub.LengthFilletRadius = 0

# Create a central bore
bore = body.newObject("PartDesign::Pocket", "Bore")
bore.Profile = doc.addObject("Part::Circle", "BoreProfile")
bore.Profile.Radius = 6  # Half of the shaft diameter
bore.Length = 25  # Overall width
bore.LengthFilletRadius = 0

# Set properties
doc.GearBody.Profile.Radius = 60
doc.GearBody.Length = 123
doc.Hub.Profile.Radius = 27.5
doc.Hub.Length = 10
doc.Bore.Profile.Radius = 6
doc.Bore.Length = 25

# Save the document
doc.saveAs("/app/answer.FCStd")
