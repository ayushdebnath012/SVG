import FreeCAD
import Part
import PartDesign
import math

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create the toothed gear body
gear = body.newObject("PartDesign::Gear", "Gear")
gear.NumberOfTeeth = 20
gear.GearModule = 1
gear.PressureAngle = 20
gear.PitchDiameter = 20
gear.OuterDiameter = 22
gear.FaceWidth = 10

# Create the central bore
bore = body.newObject("PartDesign::Cylinder", "Bore")
bore.Radius = 6 / 2
bore.Height = 20

# Create the hub
hub = body.newObject("PartDesign::Cylinder", "Hub")
hub.Radius = 16 / 2
hub.Height = 10

# Position the bore and hub
bore.Placement.Base = FreeCAD.Vector(0, 0, 0)
hub.Placement.Base = FreeCAD.Vector(0, 0, 10)

# Fuse the gear, bore, and hub
final_shape = Part.makeCompound([gear.Shape, bore.Shape, hub.Shape])
final_body = body.newObject("PartDesign::Feature", "FinalBody")
final_body.Shape = final_shape

# Save the document
doc.saveAs("/app/answer.FCStd")
