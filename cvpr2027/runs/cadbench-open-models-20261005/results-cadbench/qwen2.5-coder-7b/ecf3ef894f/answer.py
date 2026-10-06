import FreeCAD
import PartDesign

# Create a new document
doc = FreeCAD.newDocument("answer")

# Create a PartDesign Body
body = doc.addObject("PartDesign::Body", "Body")

# Define parameters
outer_diameter = 125.4125
flange_thickness = 23.01875
bolt_circle_diameter = 103.1875
mounting_hole_diameter = 13.49375
number_of_mounting_holes = 4
bore_diameter = 28.971875

# Create the flange plate
flange_plate = body.newObject("PartDesign::Pad", "FlangePlate")
flange_plate.Profile = Part.makeCircle(outer_diameter / 2)
flange_plate.Length = flange_thickness
flange_plate.LengthFilletRadius = 0

# Create the through bore
through_bore = body.newObject("PartDesign::Pocket", "ThroughBore")
through_bore.Profile = Part.makeCircle(bore_diameter / 2)
through_bore.Length = flange_thickness
through_bore.LengthFilletRadius = 0
through_bore.Base = flange_plate

# Create the mounting holes
for i in range(number_of_mounting_holes):
    angle = 2 * i * 3.141592653589793 / number_of_mounting_holes
    x = (bolt_circle_diameter / 2) * FreeCAD.sin(angle)
    y = (bolt_circle_diameter / 2) * FreeCAD.cos(angle)
    mounting_hole = body.newObject("PartDesign::Pocket", f"MountingHole{i}")
    mounting_hole.Profile = Part.makeCircle(mounting_hole_diameter / 2)
    mounting_hole.Length = flange_thickness
    mounting_hole.LengthFilletRadius = 0
    mounting_hole.Base = flange_plate
    mounting_hole.Placement.Base = FreeCAD.Vector(x, y, 0)

# Save the document
doc.saveAs(__file__.replace('.py', '.FCStd'))
