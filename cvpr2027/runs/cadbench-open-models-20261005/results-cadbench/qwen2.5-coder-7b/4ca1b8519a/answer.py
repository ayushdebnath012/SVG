import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Define the key parameters
shaft_diameter = 14.0
root_diameter = 11.0
number_teeth = 6
tooth_width = 3.0
spline_thickness = 1.0

# Create a PartDesign Feature for the shaft
shaft_feature = body.newObject("PartDesign::Feature", "Shaft")
shaft_feature.Shape = Part.makeCylinder(shaft_diameter / 2, 100)
shaft_feature.Placement.Base = FreeCAD.Vector(0, 0, 0)

# Create a PartDesign Feature for the root
root_feature = body.newObject("PartDesign::Feature", "Root")
root_feature.Shape = Part.makeCylinder(root_diameter / 2, 100)
root_feature.Placement.Base = FreeCAD.Vector(0, 0, 0)

# Create a PartDesign Feature for the teeth
teeth_feature = body.newObject("PartDesign::Feature", "Teeth")
teeth_feature.Shape = Part.makeCylinder(tooth_width / 2, 100)
teeth_feature.Placement.Base = FreeCAD.Vector(0, 0, 0)

# Create a PartDesign Feature for the spline thickness
thickness_feature = body.newObject("PartDesign::Feature", "Thickness")
thickness_feature.Shape = Part.makeCylinder(spline_thickness / 2, 100)
thickness_feature.Placement.Base = FreeCAD.Vector(0, 0, 0)

# Create a PartDesign Feature for the rectangular spline
spline_feature = body.newObject("PartDesign::Feature", "RectangularSpline")
spline_feature.Shape = Part.makeBox(100, 100, 100)
spline_feature.Placement.Base = FreeCAD.Vector(0, 0, 0)

# Combine the features into a single solid
body.newObject("PartDesign::Fusion", "Fusion").Objects = [shaft_feature, root_feature, teeth_feature, thickness_feature, spline_feature]

# Save the document
doc.saveAs(__file__.replace('.py', '.FCStd'))

# Close the document
FreeCAD.closeDocument(doc.Name)
