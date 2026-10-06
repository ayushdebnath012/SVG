import FreeCAD
import PartDesign
import Part

# Define the parameters
pressure_angle = 20  # degrees
diametral_pitch = 16
number_of_teeth = 24
pitch_diameter = 38.1  # mm
outer_diameter = 41.402  # mm
overall_length = 304.8  # mm
gear_module = 25.4 / diametral_pitch  # AGMA / ISO gear geometry

# Create a new document
doc = FreeCAD.newDocument("SpurGear")

# Create a new PartDesign body
body = PartDesign.Body(doc)

# Create a new cylindrical gear blank
cylinder = PartDesign.Cylinder(doc, "Cylinder", outer_diameter / 2, overall_length, 0, 360)

# Create a new gear blank
gear_blank = PartDesign.GearBlank(doc, "GearBlank", cylinder, number_of_teeth, gear_module, pitch_diameter, pressure_angle)

# Add the gear blank to the body
body.addObject(gear_blank)

# Save the document
doc.saveAs(__file__.replace(".py", ".FCStd"))
