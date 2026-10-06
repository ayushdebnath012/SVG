import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("HexFlangeNut")

# Set the active document
FreeCAD.setActiveDocument(doc.Name)

# Define key parameters
overall_height = 16  # mm
flange_diameter = 34.5  # mm
flange_thickness = 7  # mm
hub_width = 24  # mm
inner_diameter = 16  # mm

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Create a Hexagonal Nut Body
hex_nut_body = PartDesign.Body.createHexNut(
    body,
    hub_width=hub_width,
    height=overall_height,
    thickness=flange_thickness,
    diameter=flange_diameter
)

# Create a Plain Through-Hole
plain_through_hole = PartDesign.Body.createPlainThroughHole(
    body,
    diameter=inner_diameter,
    length=overall_height
)

# Save the document
output_path = __file__.replace(".py", ".FCStd")
doc.saveAs(output_path)
