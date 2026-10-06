import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create a cylindrical gear blank
cylinder = body.newObject("PartDesign::Cylinder", "Cylinder")
cylinder.Radius = 15.876  # pitch_diameter / 2
cylinder.Height = 304.8  # overall_length

# Create a PartDesign Feature to define the gear geometry
gear = body.newObject("PartDesign::Gear", "Gear")
gear.Base = cylinder
gear.NumberOfTeeth = 20
gear.PressureAngle = 20
gear.DiametralPitch = 16
gear.GearModule = 1.5875
gear.Profile = "Involute"

# Finalize the body
body.finish()

# Save the document
doc.saveAs("/app/answer.FCStd")

# Close the document
FreeCAD.closeDocument(doc.Name)
