import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Define the parameters
outer_diameter = 9.0
inner_diameter = 3.2
thickness = 0.8

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create a PartDesign Pad
pad = body.newObject("PartDesign::Pad", "Pad")
pad.Profile = doc.addObject("Part::Circle", "Circle")
pad.Profile.Radius = (outer_diameter - thickness) / 2
pad.Length = thickness
pad.Base = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation())

# Create a PartDesign Hole
hole = body.newObject("PartDesign::Hole", "Hole")
hole.Profile = doc.addObject("Part::Circle", "HoleCircle")
hole.Profile.Radius = inner_diameter / 2
hole.Length = thickness
hole.Base = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation())

# Save the document
doc.saveAs(__file__.replace('.py', '.FCStd'))

# Close the document
FreeCAD.closeDocument(doc.Name)
