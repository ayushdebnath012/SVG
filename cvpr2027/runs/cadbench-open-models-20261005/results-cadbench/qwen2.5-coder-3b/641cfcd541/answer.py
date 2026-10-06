import FreeCAD
import PartDesign

# Define the parameters
overall_length = 9.525  # mm
hex_width_across_flats = 6.35  # mm
through_hole_diameter = 2.8448  # mm

# Create a new document
doc = FreeCAD.newDocument("HexCouplingNut")

# Create a PartDesign body
body = PartDesign.Body(doc)

# Create a hexagonal prism
hex_prism = PartDesign.Prism(doc, "HexPrism")
hex_prism.Length = overall_length
hex_prism.Width = hex_width_across_flats
hex_prism.Height = hex_width_across_flats
hex_prism.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Create a plain through hole
through_hole = PartDesign.PlainHole(doc, "ThroughHole")
through_hole.Diameter = through_hole_diameter
through_hole.Length = overall_length
through_hole.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 0))

# Add the hex prism and through hole to the body
body.addObject(hex_prism)
body.addObject(through_hole)

# Save the document
doc.saveAs("/app/answer.FCStd")
