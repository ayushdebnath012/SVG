import FreeCAD
import Part
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create a cylindrical gear stock
cylinder = body.newObject("PartDesign::Cylinder", "Cylinder")
cylinder.Radius = 31.75 / 2
cylinder.Height = 304.8

# Create a PartDesign Feature to define the gear teeth
gear_teeth = body.newObject("PartDesign::Gear", "Gear")
gear_teeth.Base = cylinder
gear_teeth.NumberOfTeeth = 40
gear_teeth.PressureAngle = 20
gear_teeth.GearModule = 0.79375
gear_teeth.DiametralPitch = 32

# Create a PartDesign Feature to addendum envelope
addendum_envelope = body.newObject("PartDesign::Pocket", "AddendumEnvelope")
addendum_envelope.Base = gear_teeth
addendum_envelope.Length = (40 + 2) / 32 * 25.4 - 31.75

# Create a PartDesign Feature to remove the addendum
remove_addendum = body.newObject("PartDesign::Pocket", "RemoveAddendum")
remove_addendum.Base = addendum_envelope
remove_addendum.Length = 0.1

# Create a PartDesign Feature to chamfer the edges
chamfer_edges = body.newObject("PartDesign::Chamfer", "ChamferEdges")
chamfer_edges.Base = remove_addendum
chamfer_edges.Length1 = 0.5
chamfer_edges.Length2 = 0.5

# Save the document
doc.saveAs("/app/answer.FCStd")

# Close the document
FreeCAD.closeDocument(doc.Name)
