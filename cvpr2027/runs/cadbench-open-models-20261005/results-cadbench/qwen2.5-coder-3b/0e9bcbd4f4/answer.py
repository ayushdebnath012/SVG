import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("HexCouplingNut")

# Set the document's active view
FreeCAD.ActiveDocument.ActiveView.setCameraPosition(FreeCAD.Vector(0, 0, 30), FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 1, 0))

# Create a new PartDesign body
body = PartDesign.Body(doc)

# Create a new PartDesign sketch
sketch = PartDesign.Sketch(doc, body)

# Define the hex width across flats and overall length
hex_width_across_flats = 17
overall_length = 30

# Create a hexagonal prism
hex_prism = sketch.makeHexagonalPrism(hex_width_across_flats, overall_length)

# Create a cylindrical hole
through_hole_diameter = 10
cylinder = sketch.makeCylinder(through_hole_diameter, overall_length)

# Create a PartDesign feature to join the hex prism and the cylinder
feature = PartDesign.Feature(doc, body)
feature.Shape = hex_prism.Shape.fuse(cylinder.Shape)

# Set the document's active view to the PartDesign view
FreeCAD.ActiveDocument.ActiveView.setActiveObject(feature.ViewObject.Name)

# Save the document
doc.saveAs("/app/answer.FCStd")
