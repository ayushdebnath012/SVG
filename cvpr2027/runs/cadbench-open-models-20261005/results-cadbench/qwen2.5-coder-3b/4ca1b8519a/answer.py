import FreeCAD
import PartDesign

# Define the parameters
shaft_diameter = 14.0
root_diameter = 11.0
number_teeth = 6
tooth_width = 3.0
spline_thickness = 1.0

# Create a new document
doc = FreeCAD.newDocument("RectangularSpline")

# Create a PartDesign body
body = PartDesign.Body(doc)

# Create a rectangular spline profile
profile = PartDesign.Profile(doc, Part.makeRectangle(shaft_diameter, tooth_width))

# Create a cylindrical boss to define the root diameter
cylinder = PartDesign.Cylinder(doc, shaft_diameter / 2, root_diameter / 2, 0, 360)

# Create a rectangular spline feature
spline_feature = PartDesign.Spline(doc, profile, cylinder, number_teeth, spline_thickness)

# Add the spline feature to the body
body.addObject(spline_feature)

# Save the document
doc.saveAs(__file__.replace(".py", ".FCStd"))
