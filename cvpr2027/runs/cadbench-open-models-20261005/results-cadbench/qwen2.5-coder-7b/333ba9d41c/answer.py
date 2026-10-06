import FreeCAD
import Part
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create the toothed gear body
gear = body.newObject("PartDesign::Gear", "Gear")
gear.NumberOfTeeth = 48
gear.Module = 1
gear.PressureAngle = 20
gear.FaceWidth = 6
gear.PitchDiameter = 48
gear.OuterDiameter = 50
gear.RootDiameter = 45.5
gear.Addendum = 1
gear.Dedendum = 1.25

# Create the central hub
hub = body.newObject("PartDesign::Cylinder", "Hub")
hub.Radius = 16 / 2
hub.Height = 8
hub.Placement.Base = FreeCAD.Vector(0, 0, 24)

# Create the round bore
bore = body.newObject("PartDesign::Cylinder", "Bore")
bore.Radius = 8 / 2
bore.Height = 50
bore.Placement.Base = FreeCAD.Vector(0, 0, 25)

# Add the hub to the gear body
body.addFeature(hub)

# Add the bore to the gear body
body.addFeature(bore)

# Save the document
doc.saveAs("/app/answer.FCStd")

# Close the document
FreeCAD.closeDocument("answer")
