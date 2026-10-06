import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create a HexagonalPrism feature
hex_prism = body.newObject("PartDesign::Pad", "HexagonalPrism")
hex_prism.Profile = doc.addObject("Part::FeaturePython", "Hexagon")
hex_prism.Profile.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))
hex_prism.Profile.Shape = Part.makePolygon([FreeCAD.Vector(-17/2, 0, 0), FreeCAD.Vector(-17/4, 17/2, 0), FreeCAD.Vector(17/4, 17/2, 0), FreeCAD.Vector(17/2, 0, 0), FreeCAD.Vector(17/4, -17/2, 0), FreeCAD.Vector(-17/4, -17/2, 0), FreeCAD.Vector(-17/2, 0, 0)])
hex_prism.Length = 30
hex_prism.LengthFilletRadius = 0

# Create a ThroughHole feature
through_hole = body.newObject("PartDesign::Pocket", "ThroughHole")
through_hole.Profile = doc.addObject("Part::Cylinder", "Cylinder")
through_hole.Profile.Radius = 10 / 2
through_hole.Profile.Height = 30
through_hole.Base = hex_prism
through_hole.Length = 10 / 2
through_hole.LengthFilletRadius = 0

# Save the document
doc.saveAs(__file__.replace('.py', '.FCStd'))
