import FreeCAD
import PartDesign

# Define the parameters
shaft_length = 1000.0  # mm
outer_diameter = 50.0  # mm
inner_diameter = 40.0  # mm
flange_diameter = 100.0  # mm
flange_thickness = 20.0  # mm
bolt_hole_diameter = 10.0  # mm
bolt_hole_circle_diameter = 80.0  # mm
number_of_bolt_holes = 4
shaft_material_thickness = 5.0  # mm

# Create a new document
doc = FreeCAD.newDocument("RearDriveShaft")

# Create the shaft
shaft = PartDesign.Body(doc)
shaft.Shape = Part.makeCylinder(shaft_length, outer_diameter, inner_diameter, 0, 360)

# Create the flanges
flange1 = PartDesign.Feature(doc)
flange1.Shape = Part.makeCylinder(flange_thickness, flange_diameter, flange_diameter, shaft_length / 2, 0)
flange2 = PartDesign.Feature(doc)
flange2.Shape = Part.makeCylinder(flange_thickness, flange_diameter, flange_diameter, -shaft_length / 2, 0)

# Create the bolt holes
for i in range(number_of_bolt_holes):
    angle = 360 / number_of_bolt_holes * i
    hole1 = PartDesign.Feature(doc)
    hole1.Shape = Part.makeCylinder(bolt_hole_diameter, bolt_hole_circle_diameter, bolt_hole_circle_diameter, shaft_length / 2 + flange_thickness / 2, angle)
    hole2 = PartDesign.Feature(doc)
    hole2.Shape = Part.makeCylinder(bolt_hole_diameter, bolt_hole_circle_diameter, bolt_hole_circle_diameter, -shaft_length / 2 - flange_thickness / 2, angle)

# Add the shaft and flanges to the body
shaft.addObject(flange1)
shaft.addObject(flange2)
shaft.addObject(hole1)
shaft.addObject(hole2)

# Save the document
output_path = __file__.replace("answer.py", "answer.FCStd")
doc.saveAs(output_path)

# Close the document
FreeCAD.closeDocument(doc.Name)
